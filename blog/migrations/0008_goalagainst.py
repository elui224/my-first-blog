# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-01 01:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_auto_20170725_0656'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoalAgainst',
            fields=[
                ('id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('tot_goals', models.PositiveIntegerField(null=True)),
            ],
            options={
                'db_table': 'blog_goal_against',
                'managed': False,
            },
        ),
    ]
