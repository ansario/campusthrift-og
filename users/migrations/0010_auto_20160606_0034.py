# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-06 00:34
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_auto_20160606_0018'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='graduated',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(default=datetime.datetime(2016, 6, 6, 0, 34, 22, 130957)),
        ),
    ]
