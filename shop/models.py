from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

# Create your models here.

ONCAMPUS = 1
OFFCAMPUS = 2
BOTH = 3

SHIPPING_CHOICES = (
    (ONCAMPUS, 'On Campus'),
    (OFFCAMPUS, 'Off Campus'),
    (BOTH, 'Both')
)

class Subcategory(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey("Category", related_name="subcategories")
    def __unicode__(self):
        return u'%s' % (self.name)

class Category(models.Model):
    name = models.CharField(max_length=50)
    def __unicode__(self):
        return u'%s' % (self.name)

class ItemImage(models.Model):
    item = models.ForeignKey("Item", related_name='images')
    image = models.FileField(upload_to='uploads/')
    rotation = models.IntegerField(default=0)


class Item(models.Model):

    # This line is required. Links UserProfile to a User model instance.
    user = models.ForeignKey(User, related_name='seller')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)])
    sold = models.BooleanField(default=False)
    shipping_price = models.DecimalField(max_digits=5,decimal_places=2,validators=[
									MinValueValidator(0)
    ])
    meeting_place = models.CharField(max_length=200, null=True, blank=True)
    category = models.CharField(max_length=200)
    sub_category = models.CharField(max_length=200)
    shipping = models.IntegerField(choices=SHIPPING_CHOICES)
    stripe_listing_fee_id = models.CharField(max_length=200)