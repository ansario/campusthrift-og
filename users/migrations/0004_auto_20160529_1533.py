# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-29 15:33
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20160529_1449'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(default=datetime.datetime(2016, 5, 29, 15, 33, 8, 952944)),
        ),
    ]
