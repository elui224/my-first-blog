# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-07 23:55
from __future__ import unicode_literals

import blog.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011_game_author_game'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeasonPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season_points', models.PositiveIntegerField()),
                ('manager_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.Team')),
                ('season_number', models.ForeignKey(default=blog.models.get_default_season_number, on_delete=django.db.models.deletion.CASCADE, to='blog.Season')),
            ],
        ),
    ]
