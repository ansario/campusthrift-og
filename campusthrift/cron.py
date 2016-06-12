import kronos
import random
from django.contrib.auth.models import User
from datetime import datetime
from datetime import timedelta
from checkout.models import OrderItem, Order
import sendgrid
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

