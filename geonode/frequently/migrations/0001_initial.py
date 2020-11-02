# flake8: noqa
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.TextField(max_length=2000, verbose_name='Question')),
                ('slug', models.SlugField(unique=True, max_length=200, verbose_name='Slug')),
                ('answer', models.TextField(null=True, verbose_name='Answer', blank=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('last_view_date', models.DateTimeField(auto_now_add=True, verbose_name='Date of last view')),
                ('amount_of_views', models.PositiveIntegerField(default=0, verbose_name='Amount of views')),
                ('fixed_position', models.PositiveIntegerField(null=True, verbose_name='Fixed position', blank=True)),
                ('upvotes', models.PositiveIntegerField(default=0, verbose_name='Upvotes')),
                ('downvotes', models.PositiveIntegerField(default=0, verbose_name='Downvotes')),
                ('published', models.BooleanField(default=False, verbose_name='is published')),
                ('submitted_by', models.EmailField(max_length=100, verbose_name='Submitted by', blank=True)),
            ],
            options={
                'ordering': ['fixed_position', 'question'],
            },
        ),
        migrations.CreateModel(
            name='EntryCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=100, verbose_name='Slug')),
                ('fixed_position', models.PositiveIntegerField(null=True, verbose_name='Fixed position', blank=True)),
                ('last_rank', models.FloatField(default=0, verbose_name='Last calculated rank')),
            ],
            options={
                'ordering': ['fixed_position', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('remark', models.TextField(verbose_name='Remark', blank=True)),
                ('submission_date', models.DateTimeField(auto_now_add=True, verbose_name='Submission date')),
                ('validation', models.CharField(max_length=1, verbose_name='Validation mood', choices=[(b'P', 'Positive'), (b'N', 'Negative')])),
                ('entry', models.ForeignKey(verbose_name='Related entry', blank=True, to='frequently.Entry', null=True, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)),
            ],
        ),
        migrations.AddField(
            model_name='entry',
            name='category',
            field=models.ManyToManyField(related_name='entries', verbose_name='Category', to='frequently.EntryCategory'),
        ),
        migrations.AddField(
            model_name='entry',
            name='owner',
            field=models.ForeignKey(verbose_name='Owner', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL),
        ),
    ]
