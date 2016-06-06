from __future__ import unicode_literals

from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from localflavor.us.us_states import STATE_CHOICES
from localflavor.us.models import USStateField
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

from base64 import b32encode
from hashlib import sha1
from random import random

from django.db.models.signals import post_save


def pkgen():

    rude = ('lol',)
    bad_pk = True
    while bad_pk:
        pk = b32encode(sha1(str(random())).digest()).lower()[:10]
        bad_pk = False
        for rw in rude:
            if pk.find(rw) >= 0: bad_pk = True
    return pk

class UserProfile(models.Model):
    # This line is required. Links UserProfile to a User model instance.
    user = models.OneToOneField(User, related_name='user')
    graduated = models.BooleanField(default=False)
    # The additional attributes we wish to include.
    primary_key = models.CharField(max_length=10, primary_key=True, default=pkgen)
    activation_key = models.CharField(max_length=40, default="0")
    key_expires = models.DateTimeField(default=datetime.now())
    # first_name = models.CharField(max_length=200)
    # last_name = models.CharField(max_length=200)
    stripe_customer_id = models.CharField(max_length=200)
    stripe_account_id = models.CharField(max_length=200)
    picture = models.FileField(upload_to='uploads/')
    school = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    graduation_year = models.IntegerField()
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = USStateField(choices=STATE_CHOICES)
    zip = models.IntegerField(max_length=200)
    listed_first_item = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)



    # Override the __unicode__() method to return out something meaningful!
#     def __unicode__(self):
#         return self.user.username
