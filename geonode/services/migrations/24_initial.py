# -*- coding: utf-8 -*-

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
                ('resourcebase_ptr', models.OneToOneField(parent_link=True, on_delete=models.CASCADE,
                                                          auto_created=True, primary_key=True, serialize=False, to='base.ResourceBase')),
                ('type', models.CharField(max_length=4, choices=[('AUTO', 'Auto-detect'), ('OWS', 'Paired WMS/WFS/WCS'), ('WMS', 'Web Map Service'), ('CSW', 'Catalogue Service'), ('REST', 'ArcGIS REST Service'), ('OGP', 'OpenGeoPortal'), ('HGL', 'Harvard Geospatial Library')])),
                ('method', models.CharField(max_length=1, choices=[('L', 'Local'), ('C', 'Cascaded'), ('H', 'Harvested'), ('I', 'Indexed'), ('X', 'Live'), ('O', 'OpenGeoPortal')])),
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
                ('parent', models.ForeignKey(related_name='service_set', blank=True,
                                             to='services.Service', on_delete=models.CASCADE, null=True)),
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
                ('layer', models.ForeignKey(to='layers.Layer', on_delete=models.CASCADE, null=True)),
                ('service', models.ForeignKey(to='services.Service', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceProfileRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(help_text='function performed by the responsible party', max_length=255, choices=[('author', 'party who authored the resource'), ('processor', 'party who has processed the data in a manner such that the resource has been modified'), ('publisher', 'party who published the resource'), ('custodian', 'party that accepts accountability and responsibility for the data and ensures         appropriate care and maintenance of the resource'), ('pointOfContact', 'party who can be contacted for acquiring knowledge about or acquisition of the resource'), ('distributor', 'party who distributes the resource'), ('user', 'party who uses the resource'), ('resourceProvider', 'party that supplies the resource'), ('originator', 'party who created the resource'), ('owner', 'party that owns the resource'), ('principalInvestigator', 'key party responsible for gathering information and conducting research')])),
                ('profiles', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('service', models.ForeignKey(to='services.Service', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='WebServiceHarvestLayersJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default='pending', max_length=10, choices=[('pending','pending'), ('failed','failed'), ('process','process')])),
                ('service', models.OneToOneField(to='services.Service', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='WebServiceRegistrationJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('base_url', models.URLField(unique=True)),
                ('type', models.CharField(max_length=4, choices=[('AUTO', 'Auto-detect'), ('OWS', 'Paired WMS/WFS/WCS'), ('WMS', 'Web Map Service'), ('CSW', 'Catalogue Service'), ('REST', 'ArcGIS REST Service'), ('OGP', 'OpenGeoPortal'), ('HGL', 'Harvard Geospatial Library')])),
                ('status', models.CharField(default='pending', max_length=10, choices=[('pending','pending'), ('failed','failed'), ('process','process')])),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='profiles',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='services.ServiceProfileRole'),
        ),
    ]
