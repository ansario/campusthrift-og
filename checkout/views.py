from django.shortcuts import render, redirect
import braintree
from shop.models import Item
from checkout.models import Order, OrderItem
from campusthrift import settings

from decimal import Decimal

braintree.Configuration.configure(braintree.Environment.Sandbox,
    merchant_id=settings.BRAINTREE_MERCHANT_ID,
    public_key=settings.BRAINTREE_PUBLIC_KEY,
    private_key=settings.BRAINTREE_PRIVATE_KEY)

def checkout(request):


    if request.method == 'GET':
        request.session['braintree_client_token'] = braintree.ClientToken.generate()

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
        return render(request, 'checkout/checkout.html', {'sold_item_list': sold_item_list, 'items': item_list, 'total':final_total, 'sub_total': total_price, 'total_shipping': total_shipping})

    else:
        nonce = request.POST["payment_method_nonce"]
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

            # try:
            #     True = False
                # return render(request, 'checkout/checkout.html',  {'errors':result.errors.deep_errors, 'items': item_list, 'total':final_total, 'sub_total': total_price, 'total_shipping': total_shipping})
            # except AttributeError:
                # del request.session['cart']
            result = braintree.PaymentMethod.create({
                "customer_id": request.user.user.braintree_customer_id,
                "payment_method_nonce": nonce
            })



            new_order = Order()
            new_order.payment = result.payment_method.token
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

                if new_order_item.shipping_method == 1:
                    new_order_item.shipping_price = 0.00
                    new_order_item.order_item_total_price = new_order_item.price
                else:
                    new_order_item.shipping_price = item.shipping_price
                    shipping_total = shipping_total + item.shipping_price
                    new_order_item.order_item_total_price = new_order_item.price + new_order_item.shipping_price


                sub_total = sub_total + item.price
                new_order_item.save()











            new_order.final_total = sub_total + shipping_total
            new_order.shipping_total = shipping_total
            new_order.sub_total = sub_total
            new_order.save()



            request.session['order'] = new_order.primary_key


            return redirect('confirm')


def confirm(request):
    order_key = request.session['order']
    order = Order.objects.get(primary_key=order_key)
    if request.method == 'GET':


        order_items = order.orders.all()
        return render(request, 'checkout/confirm.html', {'order': order, 'order_items': order_items})
    else:
        order.confirmed = True
        order.save()



        for order_item in order.orders.all():

           order_item.item.sold = True
           order_item.item.save()

           TWOPLACES = Decimal(10) ** -2

           result = braintree.Transaction.sale({
                "merchant_account_id": order_item.item.user.user.braintree_merchant_id,
                "amount": order_item.order_item_total_price,
                "customer_id": request.user.user.braintree_customer_id,
                "service_fee_amount": str(Decimal(order_item.order_item_total_price * Decimal(0.2)).quantize(TWOPLACES)),
                "options": {
                  "submit_for_settlement": True,
                },

            })

           escrow_result = braintree.Transaction.hold_in_escrow(result.transaction.id)
           print escrow_result.transaction.escrow_status
           testing_gateway = braintree.TestingGateway(braintree.Configuration.gateway())
           testing_gateway.settle_transaction(result.transaction.id)
           testing_gateway.settlement_confirm_transaction(result.transaction.id)

           updated_transaction = braintree.Transaction.find(result.transaction.id)
           print updated_transaction.escrow_status
           order_item.braintree_id_transaction = result.transaction.id
           order_item.save()
        del request.session['cart']
        return redirect('thanks')

def thanks(request):
    return render(request, 'checkout/thanks.html')


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