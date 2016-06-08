from __future__ import unicode_literals
from datetime import datetime
from django.db import models
from base64 import b32encode
from hashlib import sha1
from random import random
from shop.models import Item
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


ONCAMPUS = 1
OFFCAMPUS = 2
BOTH = 3

SHIPPING_CHOICES = (
    (ONCAMPUS, 'On Campus'),
    (OFFCAMPUS, 'Off Campus'),
    (BOTH, 'Both')
)

def pkgen():

    rude = ('lol',)
    bad_pk = True
    while bad_pk:
        pk = b32encode(sha1(str(random())).digest()).lower()[:10]
        bad_pk = False
        for rw in rude:
            if pk.find(rw) >= 0: bad_pk = True
    return pk

# Create your models here.
class Order(models.Model):

    buyer = models.ForeignKey(User, related_name='item_buyer')
    date = models.DateTimeField(default=datetime.now())
    primary_key = models.CharField(max_length=10, primary_key=True, default=pkgen)
    confirmed = models.BooleanField(default=False)
    payment_confirmed = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)
    in_progress = models.BooleanField(default=False)
    canceled = models.BooleanField(default=False)
    sub_total = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)])
    shipping_total = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)])
    final_total = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)])
    shipping_address = models.CharField(max_length=500)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zip = models.CharField(max_length=200)

class OrderItem(models.Model):

    seller = models.ForeignKey(User, related_name='item_seller')

    order = models.ForeignKey("Order", related_name="orders")
    item = models.ForeignKey(Item, related_name="item")
    shipping_method = models.IntegerField(choices=SHIPPING_CHOICES)
    shipping_price = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)])
    price = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)])
    order_item_total_price = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)])
    seller_confirmed = models.BooleanField(default=False)
    buyer_confirmed = models.BooleanField(default=False)
    stripe_charge_id = models.CharField(max_length=200)
