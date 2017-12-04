# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-27 01:06
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_usersession'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersession',
            name='user',
            field=models.ForeignKey(blank=True, null=True,on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
