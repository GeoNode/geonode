# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '__first__'),
        ('layers', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('resourcebase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='base.ResourceBase')),
                ('type', models.CharField(max_length=4, choices=[(b'AUTO', 'Auto-detect'), (b'OWS', 'Paired WMS/WFS/WCS'), (b'WMS', 'Web Map Service'), (b'CSW', 'Catalogue Service'), (b'REST', 'ArcGIS REST Service'), (b'OGP', 'OpenGeoPortal'), (b'HGL', 'Harvard Geospatial Library')])),
                ('method', models.CharField(max_length=1, choices=[(b'L', 'Local'), (b'C', 'Cascaded'), (b'H', 'Harvested'), (b'I', 'Indexed'), (b'X', 'Live'), (b'O', 'OpenGeoPortal')])),
                ('base_url', models.URLField(unique=True, db_index=True)),
                ('version', models.CharField(max_length=10, null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=255, db_index=True)),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('online_resource', models.URLField(null=True, verbose_name=False, blank=True)),
                ('fees', models.CharField(max_length=1000, null=True, blank=True)),
                ('access_constraints', models.CharField(max_length=255, null=True, blank=True)),
                ('connection_params', models.TextField(null=True, blank=True)),
                ('username', models.CharField(max_length=50, null=True, blank=True)),
                ('password', models.CharField(max_length=50, null=True, blank=True)),
                ('api_key', models.CharField(max_length=255, null=True, blank=True)),
                ('workspace_ref', models.URLField(null=True, verbose_name=False, blank=True)),
                ('store_ref', models.URLField(null=True, blank=True)),
                ('resources_ref', models.URLField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('first_noanswer', models.DateTimeField(null=True, blank=True)),
                ('noanswer_retries', models.PositiveIntegerField(null=True, blank=True)),
                ('external_id', models.IntegerField(null=True, blank=True)),
                ('parent', models.ForeignKey(related_name='service_set', blank=True, to='services.Service', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('base.resourcebase',),
        ),
        migrations.CreateModel(
            name='ServiceLayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typename', models.CharField(max_length=255, verbose_name='Layer Name')),
                ('title', models.CharField(max_length=512, verbose_name='Layer Title')),
                ('description', models.TextField(null=True, verbose_name='Layer Description')),
                ('styles', models.TextField(null=True, verbose_name='Layer Styles')),
                ('layer', models.ForeignKey(to='layers.Layer', null=True)),
                ('service', models.ForeignKey(to='services.Service')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceProfileRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(help_text='function performed by the responsible party', max_length=255, choices=[(b'author', 'party who authored the resource'), (b'processor', 'party who has processed the data in a manner such that the resource has been modified'), (b'publisher', 'party who published the resource'), (b'custodian', 'party that accepts accountability and responsibility for the data and ensures         appropriate care and maintenance of the resource'), (b'pointOfContact', 'party who can be contacted for acquiring knowledge about or acquisition of the resource'), (b'distributor', 'party who distributes the resource'), (b'user', 'party who uses the resource'), (b'resourceProvider', 'party that supplies the resource'), (b'originator', 'party who created the resource'), (b'owner', 'party that owns the resource'), (b'principalInvestigator', 'key party responsible for gathering information and conducting research')])),
                ('profiles', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('service', models.ForeignKey(to='services.Service')),
            ],
        ),
        migrations.CreateModel(
            name='WebServiceHarvestLayersJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'pending', max_length=10, choices=[(b'pending', b'pending'), (b'failed', b'failed'), (b'process', b'process')])),
                ('service', models.OneToOneField(to='services.Service')),
            ],
        ),
        migrations.CreateModel(
            name='WebServiceRegistrationJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('base_url', models.URLField(unique=True)),
                ('type', models.CharField(max_length=4, choices=[(b'AUTO', 'Auto-detect'), (b'OWS', 'Paired WMS/WFS/WCS'), (b'WMS', 'Web Map Service'), (b'CSW', 'Catalogue Service'), (b'REST', 'ArcGIS REST Service'), (b'OGP', 'OpenGeoPortal'), (b'HGL', 'Harvard Geospatial Library')])),
                ('status', models.CharField(default=b'pending', max_length=10, choices=[(b'pending', b'pending'), (b'failed', b'failed'), (b'process', b'process')])),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='profiles',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='services.ServiceProfileRole'),
        ),
    ]
