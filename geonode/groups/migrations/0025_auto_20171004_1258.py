# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '24_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('answered', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserInvitationModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.CharField(default=b'free', max_length=10, choices=[(b'pending', 'Pending'), (b'free', 'Free'), (b'connected', 'Connected')])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 4, 12, 58, 51, 132069), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='docked',
            field=models.BooleanField(default=False, help_text='Should this organization be docked in home page?', verbose_name='Docked'),
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='favorite',
            field=models.BooleanField(default=False, help_text='Should this organization be in favorite list ?', verbose_name='Favorite'),
        ),
        migrations.AlterField(
            model_name='groupprofile',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='userinvitationmodel',
            name='group',
            field=models.ForeignKey(to='groups.GroupProfile'),
        ),
        migrations.AddField(
            model_name='userinvitationmodel',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='questionanswer',
            name='group',
            field=models.ForeignKey(blank=True, to='groups.GroupProfile', null=True),
        ),
        migrations.AddField(
            model_name='questionanswer',
            name='questioner',
            field=models.ForeignKey(related_name='questioner', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='questionanswer',
            name='respondent',
            field=models.ForeignKey(related_name='respondent', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='userinvitationmodel',
            unique_together=set([('group', 'user', 'state')]),
        ),
    ]
