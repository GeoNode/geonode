# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0028_auto_20170919_1550'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name=b'title')),
                ('abstract', models.TextField(verbose_name=b'abstract', blank=True)),
                ('delimiter', models.CharField(default=b'', max_length=6)),
                ('table_name', models.CharField(unique=True, max_length=255)),
                ('tablespace', models.CharField(max_length=255, verbose_name=b'database')),
                ('uploaded_file', models.FileField(upload_to=b'datatables/%Y/%m/%d')),
                ('create_table_sql', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DataTableAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attribute', models.CharField(max_length=255, null=True, verbose_name='Attribute Name')),
                ('attribute_label', models.CharField(max_length=255, null=True, verbose_name='Attribute Label')),
                ('attribute_type', models.CharField(default=b'xsd:string', max_length=50, verbose_name='Attribute Type')),
                ('searchable', models.BooleanField(default=False, verbose_name='Searchable?')),
                ('visible', models.BooleanField(default=True, verbose_name='Visible?')),
                ('display_order', models.IntegerField(default=1, verbose_name='Display Order')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('datatable', models.ForeignKey(related_name='attribute_set', to='datatables.DataTable')),
            ],
        ),
        migrations.CreateModel(
            name='GeocodeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Examples: US Census Block, US County FIPS code, US Zip code, etc', unique=True, max_length=50)),
                ('description', models.CharField(help_text=b'Short description for end user', max_length=255, blank=True)),
                ('sort_order', models.IntegerField(default=10)),
                ('slug', models.SlugField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('sort_order', 'name'),
            },
        ),
        migrations.CreateModel(
            name='JoinTarget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Will be presented to Geoconnect Users. e.g. "Boston Zip Codes (5 digit)"', max_length=100)),
                ('year', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('attribute', models.ForeignKey(to='layers.Attribute')),
            ],
            options={
                'ordering': ('year', 'name'),
            },
        ),
        migrations.CreateModel(
            name='JoinTargetFormatType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Census Tract (6 digits, no decimal)', max_length=255)),
                ('is_zero_padded', models.BooleanField(default=False)),
                ('expected_zero_padded_length', models.IntegerField(default=-1)),
                ('description', models.TextField(help_text=b'verbal description for client. e.g. Remove non integers. Check for empty string. Pad with zeros until 6 digits.')),
                ('regex_match_string', models.CharField(help_text=b"r'\\d{6}'; Usage: re.search(r'\\d{6}', your_input)", max_length=255, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='LatLngTableMappingRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mapped_record_count', models.IntegerField(default=0, help_text=b'Records mapped')),
                ('unmapped_record_count', models.IntegerField(default=0, help_text=b'Records that failed to map Lat/Lng')),
                ('unmapped_records_list', models.TextField(help_text=b'Unmapped records', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('datatable', models.ForeignKey(to='datatables.DataTable')),
                ('lat_attribute', models.ForeignKey(related_name='lat_attribute', to='datatables.DataTableAttribute')),
                ('layer', models.ForeignKey(related_name='lat_lng_records', blank=True, to='layers.Layer', null=True)),
                ('lng_attribute', models.ForeignKey(related_name='lng_attribute', to='datatables.DataTableAttribute')),
            ],
            options={
                'verbose_name': 'Latitude/Longitude Table Mapping Record',
            },
        ),
        migrations.CreateModel(
            name='TableJoin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('view_name', models.CharField(max_length=255, null=True, blank=True)),
                ('view_sql', models.TextField(null=True, blank=True)),
                ('matched_records_count', models.IntegerField(null=True, blank=True)),
                ('unmatched_records_count', models.IntegerField(null=True, blank=True)),
                ('unmatched_records_list', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('datatable', models.ForeignKey(to='datatables.DataTable')),
                ('join_layer', models.ForeignKey(related_name='join_layer', blank=True, to='layers.Layer', null=True)),
                ('layer_attribute', models.ForeignKey(related_name='layer_attribute', to='layers.Attribute')),
                ('source_layer', models.ForeignKey(related_name='source_layer', to='layers.Layer')),
                ('table_attribute', models.ForeignKey(related_name='table_attribute', to='datatables.DataTableAttribute')),
            ],
        ),
        migrations.AddField(
            model_name='jointarget',
            name='expected_format',
            field=models.ForeignKey(to='datatables.JoinTargetFormatType'),
        ),
        migrations.AddField(
            model_name='jointarget',
            name='geocode_type',
            field=models.ForeignKey(to='datatables.GeocodeType', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='jointarget',
            name='layer',
            field=models.ForeignKey(to='layers.Layer'),
        ),
        migrations.AlterUniqueTogether(
            name='jointarget',
            unique_together=set([('layer', 'attribute')]),
        ),
    ]
