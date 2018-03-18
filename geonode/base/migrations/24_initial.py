# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import geonode.security.models
import datetime
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(help_text='function performed by the responsible party', max_length=255, choices=[(b'author', 'party who authored the resource'), (b'processor', 'party who has processed the data in a manner such that the resource has been modified'), (b'publisher', 'party who published the resource'), (b'custodian', 'party that accepts accountability and responsibility for the data and ensures         appropriate care and maintenance of the resource'), (b'pointOfContact', 'party who can be contacted for acquiring knowledge about or acquisition of the resource'), (b'distributor', 'party who distributes the resource'), (b'user', 'party who uses the resource'), (b'resourceProvider', 'party that supplies the resource'), (b'originator', 'party who created the resource'), (b'owner', 'party that owns the resource'), (b'principalInvestigator', 'key party responsible for gathering information and conducting research')])),
                ('contact', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100, null=True)),
                ('abbreviation', models.CharField(max_length=20, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('description_en', models.TextField(null=True, blank=True)),
                ('url', models.URLField(max_length=2000, null=True, blank=True)),
                ('license_text', models.TextField(null=True, blank=True)),
                ('license_text_en', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Licenses',
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extension', models.CharField(help_text='For example "kml"', max_length=255)),
                ('link_type', models.CharField(max_length=255, choices=[(b'original', b'original'), (b'data', b'data'), (b'image', b'image'), (b'metadata', b'metadata'), (b'html', b'html'), (b'OGC:WMS', b'OGC:WMS'), (b'OGC:WFS', b'OGC:WFS'), (b'OGC:WCS', b'OGC:WCS')])),
                ('name', models.CharField(help_text='For example "View in Google Earth"', max_length=255)),
                ('mime', models.CharField(help_text='For example "text/xml"', max_length=255)),
                ('url', models.TextField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=50)),
                ('name', models.CharField(max_length=255)),
                ('name_en', models.CharField(max_length=255, null=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='base.Region', null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Metadata Regions',
            },
        ),
        migrations.CreateModel(
            name='RestrictionCodeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('description', models.TextField(max_length=255, editable=False)),
                ('description_en', models.TextField(max_length=255, null=True, editable=False)),
                ('gn_description', models.TextField(max_length=255, verbose_name=b'GeoNode description')),
                ('gn_description_en', models.TextField(max_length=255, null=True, verbose_name=b'GeoNode description')),
                ('is_choice', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Metadata Restriction Code Types',
            },
        ),
        migrations.CreateModel(
            name='SpatialRepresentationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('description', models.CharField(max_length=255, editable=False)),
                ('description_en', models.CharField(max_length=255, null=True, editable=False)),
                ('gn_description', models.CharField(max_length=255, verbose_name=b'GeoNode description')),
                ('gn_description_en', models.CharField(max_length=255, null=True, verbose_name=b'GeoNode description')),
                ('is_choice', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Metadata Spatial Representation Types',
            },
        ),
        migrations.CreateModel(
            name='TopicCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(default=b'location', max_length=255)),
                ('description', models.TextField(default=b'')),
                ('description_en', models.TextField(default=b'', null=True)),
                ('gn_description', models.TextField(default=b'', null=True, verbose_name=b'GeoNode description')),
                ('gn_description_en', models.TextField(default=b'', null=True, verbose_name=b'GeoNode description')),
                ('is_choice', models.BooleanField(default=True))
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Metadata Topic Categories',
            },
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='category',
            field=models.ForeignKey(blank=True, to='base.TopicCategory', help_text='high-level geographic data thematic classification to assist in the grouping and search of available geographic data sets.', null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='contacts',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='base.ContactRole'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='license',
            field=models.ForeignKey(blank=True, to='base.License', help_text='license of the dataset', null=True, verbose_name='License'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='owner',
            field=models.ForeignKey(related_name='owned_resource', verbose_name='Owner', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_base.resourcebase_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='regions',
            field=models.ManyToManyField(help_text='keyword identifies a location', to='base.Region', verbose_name='keywords region', blank=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='restriction_code_type',
            field=models.ForeignKey(blank=True, to='base.RestrictionCodeType', help_text='limitation(s) placed upon the access or use of the data.', null=True, verbose_name='restrictions'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='spatial_representation_type',
            field=models.ForeignKey(blank=True, to='base.SpatialRepresentationType', help_text='method used to represent geographic information in the dataset.', null=True, verbose_name='spatial representation type'),
        ),
        migrations.AddField(
            model_name='link',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AddField(
            model_name='contactrole',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='contactrole',
            unique_together=set([('contact', 'resource', 'role')]),
        ),
    ]
