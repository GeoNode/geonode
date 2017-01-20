# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupInvitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(max_length=40)),
                ('email', models.EmailField(max_length=254)),
                ('role', models.CharField(max_length=10, choices=[(b'manager', 'Manager'), (b'member', 'Member')])),
                ('state', models.CharField(default=b'sent', max_length=10, choices=[(b'sent', 'Sent'), (b'accepted', 'Accepted'), (b'declined', 'Declined')])),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('from_user', models.ForeignKey(related_name='pg_invitations_sent', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=10, choices=[(b'manager', 'Manager'), (b'member', 'Member')])),
                ('joined', models.DateTimeField(default=datetime.datetime.now)),
            ],
        ),
        migrations.CreateModel(
            name='GroupProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=50, verbose_name='Title')),
                ('slug', models.SlugField(unique=True)),
                ('logo', models.ImageField(upload_to=b'people_group', verbose_name='Logo', blank=True)),
                ('description', models.TextField(verbose_name='Description')),
                ('email', models.EmailField(help_text='Email used to contact one or all group members, such as a mailing list, shared email, or exchange group.', max_length=254, null=True, verbose_name='Email', blank=True)),
                ('access', models.CharField(default=b"public'", help_text='Public: Any registered user can view and join a public group.<br>Public (invite-only):Any registered user can view the group.  Only invited users can join.<br>Private: Registered users cannot see any details about the group, including membership.  Only invited users can join.', max_length=15, verbose_name='Access', choices=[(b'public', 'Public'), (b'public-invite', 'Public (invite-only)'), (b'private', 'Private')])),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('group', models.OneToOneField(to='auth.Group')),
                ('keywords', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A space or comma-separated list of keywords', verbose_name='Keywords')),
            ],
        ),
        migrations.AddField(
            model_name='groupmember',
            name='group',
            field=models.ForeignKey(to='groups.GroupProfile'),
        ),
        migrations.AddField(
            model_name='groupmember',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupinvitation',
            name='group',
            field=models.ForeignKey(related_name='invitations', to='groups.GroupProfile'),
        ),
        migrations.AddField(
            model_name='groupinvitation',
            name='user',
            field=models.ForeignKey(related_name='pg_invitations_received', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='groupinvitation',
            unique_together=set([('group', 'email')]),
        ),
    ]
