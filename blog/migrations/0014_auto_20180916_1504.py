# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-16 20:04
from __future__ import unicode_literals

import blog.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0013_auto_20180915_0607'),
    ]

    operations = [
        migrations.AddField(
            model_name='assist',
            name='fifa_year',
            field=models.ForeignKey(default=blog.models.get_current_year_number, null=True, on_delete=django.db.models.deletion.CASCADE, to='blog.Year'),
        ),
        migrations.AddField(
            model_name='goal',
            name='fifa_year',
            field=models.ForeignKey(default=blog.models.get_current_year_number, null=True, on_delete=django.db.models.deletion.CASCADE, to='blog.Year'),
        ),
    ]
