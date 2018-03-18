# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IndexPageImagesModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('descripton', models.TextField(max_length=300, null=True, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('image', models.ImageField(upload_to=b'')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SectionManagementModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=500)),
                ('slug', models.SlugField(max_length=100, null=True, blank=True)),
                ('section_sub_title', models.CharField(max_length=500)),
                ('description', models.TextField(max_length=1000, null=True, blank=True)),
                ('image1', models.ImageField(null=True, upload_to=b'index_page/section_images', blank=True)),
                ('image2', models.ImageField(null=True, upload_to=b'index_page/section_images', blank=True)),
                ('image3', models.ImageField(null=True, upload_to=b'index_page/section_images', blank=True)),
                ('image4', models.ImageField(null=True, upload_to=b'index_page/section_images', blank=True)),
                ('image5', models.ImageField(null=True, upload_to=b'index_page/section_images', blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('background_image', models.ImageField(null=True, upload_to=b'', blank=True)),
                ('background_color', models.CharField(max_length=20, null=True, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SectionManagementTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'', max_length=50)),
                ('slug', models.SlugField(max_length=100, null=True, blank=True)),
                ('is_visible', models.BooleanField(default=True)),
                ('should_update', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SliderImages',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('descripton', models.TextField(max_length=300)),
                ('is_active', models.BooleanField(default=False)),
                ('image', models.ImageField(upload_to=b'index_page/slider_images')),
                ('logo_url', models.URLField(null=True, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('section', models.ForeignKey(blank=True, to='cms.SectionManagementTable', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='indexpageimagesmodel',
            name='section',
            field=models.ForeignKey(blank=True, to='cms.SectionManagementTable', null=True),
        ),
    ]
