# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0003_auto_20160815_0504'),
        ('base', '0002_auto_20160810_0827'),
    ]

    operations = [
        migrations.CreateModel(
            name='DockedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(blank=True, to='groups.GroupProfile', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FavoriteResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(blank=True, to='groups.GroupProfile', null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='resourcebase',
            name='docked',
        ),
        migrations.RemoveField(
            model_name='resourcebase',
            name='favorite',
        ),
        migrations.AddField(
            model_name='favoriteresource',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AddField(
            model_name='favoriteresource',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dockedresource',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AddField(
            model_name='dockedresource',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
