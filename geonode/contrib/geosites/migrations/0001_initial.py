# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('base', '0029_auto_20171114_0341'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '26_to_27'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteGroups',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ManyToManyField(to='groups.GroupProfile', null=True, blank=True)),
                ('site', models.OneToOneField(to='sites.Site')),
            ],
            options={
                'verbose_name_plural': 'Site Group',
            },
        ),
        migrations.CreateModel(
            name='SitePeople',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('people', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('site', models.OneToOneField(to='sites.Site')),
            ],
            options={
                'verbose_name_plural': 'Site People',
            },
        ),
        migrations.CreateModel(
            name='SiteResources',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resources', models.ManyToManyField(to='base.ResourceBase', null=True, blank=True)),
                ('site', models.OneToOneField(to='sites.Site')),
            ],
            options={
                'verbose_name_plural': 'Site Resources',
            },
        ),
    ]
