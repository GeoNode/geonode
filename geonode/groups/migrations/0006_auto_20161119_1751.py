# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0005_auto_20161023_1415'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserInvitationModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.CharField(default=b'free', max_length=10, choices=[(b'pending', 'Pending'), (b'free', 'Free'), (b'connected', 'Connected')])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(to='groups.GroupProfile')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userinvitationmodel',
            unique_together=set([('group', 'user', 'state')]),
        ),
    ]
