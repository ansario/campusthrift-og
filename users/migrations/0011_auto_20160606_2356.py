# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-06 23:56
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20160606_0034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(default=datetime.datetime(2016, 6, 6, 23, 56, 10, 414855)),
        ),
    ]
