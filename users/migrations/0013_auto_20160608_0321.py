# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-08 03:21
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_auto_20160606_2356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(default=datetime.datetime(2016, 6, 8, 3, 21, 33, 9871)),
        ),
    ]
