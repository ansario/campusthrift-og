import kronos
import random
from django.contrib.auth.models import User
from datetime import datetime
from datetime import timedelta
from checkout.models import OrderItem, Order
import sendgrid
import stripe
stripe.api_key = STRIPE_API_KEY
import os
from campusthrift.settings import PROJECT_ROOT, HOSTED_URL, SG_KEY
sg = sendgrid.SendGridClient(SG_KEY)

@kronos.register('0 0 * * *')

def reminder_email():


    base_reminder_email_template = open(os.path.join(PROJECT_ROOT, 'emails/reminder_email.html')).read()

    orders = Order.objects.all().filter(date__gte=datetime.now()-timedelta(days=3), complete=False)

    for order in orders:
        order_items = OrderItem.objects.all().filter(order=order)
        for item in order_items:

            message = sendgrid.Mail(to=item.seller.email, subject='CampusThrift Buyer Reminder', html=base_reminder_email_template, text='Body', from_email='noreply@campusthrift.com')
            sg.send(message)

@kronos.register('0 0 * * *')
def process_sales():

    orders = Order.objects.all().filter(date__gte=datetime.now()-timedelta(days=6))

    for order in orders:
        order_items = OrderItem.objects.all().filter(order=order)


        for item in order_items:
            if item.seller_confirmed and not item.buyer_confirmed:
                item.buyer_confirmed = True

                seller_stripe_account = stripe.Account.retrieve(item.seller.user.stripe_account_id)


                stripe.Transfer.create(
                    amount = int((float(item.order_item_total_price) * 100 * .88) - ((float(item.order_item_total_price) * 100 * .029) + 30)),
                    currency = "usd",
                    destination = seller_stripe_account,
                    description = "Transfer for " + item.seller.email,
                    source_transaction=item.stripe_charge_id
                )

                item.save()

        order.complete = True
        order.save()

@kronos.register('0 0 * * *')
def process_graduates():

    users = User.objects.all()

    for user in users:
        current_year = datetime.now().year
        if user.user.graduation_year < current_year - 1:
            user.user.graduated = True
            user.user.save()

