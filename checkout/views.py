from django.shortcuts import render, redirect
import braintree
import stripe
from shop.models import Item
from checkout.models import Order, OrderItem
from campusthrift import settings
from django.contrib.auth.decorators import login_required
import sendgrid
import os
from campusthrift.settings import PROJECT_ROOT, HOSTED_URL, SG_KEY, STRIPE_API_KEY
#sg = sendgrid.SendGridClient(SG_KEY)
stripe.api_key = STRIPE_API_KEY
from decimal import Decimal

braintree.Configuration.configure(braintree.Environment.Sandbox,
    merchant_id=settings.BRAINTREE_MERCHANT_ID,
    public_key=settings.BRAINTREE_PUBLIC_KEY,
    private_key=settings.BRAINTREE_PRIVATE_KEY)

@login_required(login_url='/login')
def checkout(request):


    if request.method == 'GET':
        # request.session['braintree_client_token'] = braintree.ClientToken.generate()
        stripe_customer = stripe.Customer.retrieve(request.user.user.stripe_customer_id)
        payment_info = stripe_customer.sources.retrieve(stripe_customer.default_source)
        cart = request.session.get('cart', {})
        new_cart = cart.copy()
        item_list = []
        sold_item_list = []
        total_price = 0
        total_shipping = 0
        for id in cart:
            try:
                item = Item.objects.get(pk=id)
                if item.sold == True:
                    sold_item_list.append(item)
                    del new_cart[id]

                else:
                    item_list.append(item)
                    total_price = total_price + item.price
                    total_shipping = total_shipping + item.shipping_price
            except:
                pass

        final_total = total_shipping + total_price
        if sold_item_list:
            request.session['cart'] = new_cart
        return render(request, 'checkout/checkout.html', {'sold_item_list': sold_item_list, 'items': item_list, 'total':final_total, 'sub_total': total_price, 'total_shipping': total_shipping, 'payment_information': payment_info})

    else:

        print request.POST
        cart = request.session.get('cart', {})
        new_cart = cart.copy()
        item_list = []
        sold_item_list = []

        total_price = 0
        total_shipping = 0
        final_total = 0
        print cart
        print new_cart

        for id in cart:
            try:
                item = Item.objects.get(pk=id)
                if item.sold == True:
                    sold_item_list.append(item)

                    base_sold_email_template = open(os.path.join(PROJECT_ROOT, 'emails/reminder_email.html')).read()
                    message = sendgrid.Mail(to=item.seller.email, subject='CampusThrift Buyer Reminder', html=base_sold_email_template, text='Body', from_email='noreply@campusthrift.com')
                    sg.send(message)

                    del new_cart[id]

                else:
                    item_list.append(item)
                    total_price = total_price + item.price
                    total_shipping = total_shipping + item.shipping_price
            except:
                pass

        final_total = total_shipping + total_price




        if sold_item_list:
            request.session['cart'] = new_cart
            return render(request, 'checkout/checkout.html',  {'sold_item_list': sold_item_list, 'items': item_list, 'total':final_total, 'sub_total': total_price, 'total_shipping': total_shipping})
        else:


            new_order = Order()
            new_order.buyer = request.user

            sub_total = 0
            shipping_total = 0
            final_total = 0

            #
            for item in item_list:
                new_order_item = OrderItem()
                new_order_item.order = new_order
                new_order_item.item = item
                new_order_item.seller = item.user
                new_order_item.shipping_method = request.POST[str(item.pk) + '_ship_method']
                new_order_item.price = item.price

                if int(request.POST[str(item.pk) + '_ship_method']) == 1:
                    new_order_item.shipping_price = 0.00
                    new_order_item.order_item_total_price = new_order_item.price
                else:

                    new_order_item.shipping_price = item.shipping_price
                    shipping_total = shipping_total + item.shipping_price
                    new_order_item.order_item_total_price = new_order_item.price + new_order_item.shipping_price


                sub_total = sub_total + item.price



                new_order_item.save()

            new_order.shipping_address = request.POST['address']
            new_order.city = request.POST['city']
            new_order.state = request.POST['state']
            new_order.zip = request.POST['zip']

            new_order.final_total = sub_total + shipping_total
            new_order.shipping_total = shipping_total
            new_order.sub_total = sub_total
            new_order.save()



            request.session['order'] = new_order.primary_key


            return redirect('confirm')

@login_required(login_url='/login')
def confirm(request):
    order_key = request.session['order']
    order = Order.objects.get(primary_key=order_key)
    if request.method == 'GET':


        order_items = order.orders.all()
        return render(request, 'checkout/confirm.html', {'order': order, 'order_items': order_items})
    else:
        order.confirmed = False
        order.save()



        for order_item in order.orders.all():

           order_item.item.sold = True
           order_item.item.save()


           result = stripe.Charge.create(
               amount = int(order_item.order_item_total_price * 100),
               currency = "usd",
               customer = request.user.user.stripe_customer_id,
               description = "charge for " + request.user.email,
           )


           order_item.stripe_charge_id = result.id
           order_item.save()

           order.payment_confirmed = True


        del request.session['cart']
        return redirect('thanks')

#@login_required(login_url='/login')
def thanks(request):
    return render(request, 'checkout/thanks.html')
    #return render( 'checkout/thanks.html')

@login_required(login_url='/login')
def payment(request):
    if request.method == 'GET':
        request.session['braintree_client_token'] = braintree.ClientToken.generate()
        return render(request, 'checkout/payment.html')

    else:
        for key in request.POST:
            print(key)
            value = request.POST[key]
            print(value)
        return render(request, 'checkout/payment.html')
