# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-27 01:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0006_auto_20171127_0918'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersession',
            name='user',
        ),
    ]
