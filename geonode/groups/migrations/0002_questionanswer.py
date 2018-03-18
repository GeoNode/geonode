# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.TextField(help_text='Ask a question')),
                ('answer', models.TextField(help_text='Answer the question')),
                ('answered', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(blank=True, to='groups.GroupProfile', null=True)),
                ('questioner', models.ForeignKey(related_name='questioner', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('respondent', models.ForeignKey(related_name='respondent', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
