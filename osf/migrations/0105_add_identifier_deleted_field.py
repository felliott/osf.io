# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-18 19:14
from __future__ import unicode_literals

from django.db import migrations
import osf.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0104_merge_20180518_1337'),
    ]

    operations = [
        migrations.AddField(
            model_name='identifier',
            name='deleted',
            field=osf.utils.fields.NonNaiveDateTimeField(blank=True, null=True),
        ),
    ]
