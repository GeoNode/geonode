# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_topiccategory_fa_class'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='distribution_description',
            field=models.TextField(help_text='detailed text description of what the online resource is/does', null=True, verbose_name='distribution description', blank=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='distribution_url',
            field=models.TextField(help_text='information about on-line sources from which the dataset, specification, or community profile name and extended metadata elements can be obtained', null=True, verbose_name='distribution URL', blank=True),
        ),
        migrations.AlterField(
            model_name='contactrole',
            name='role',
            field=models.CharField(help_text='function performed by the responsible party', max_length=255, choices=[(b'author', 'party who authored the resource'), (b'processor', 'party who has processed the data in a manner such that the resource has been modified'), (b'publisher', 'party who published the resource'), (b'custodian', 'party that accepts accountability and responsibility for the data and ensures         appropriate care and maintenance of the resource'), (b'pointOfContact', 'party who can be contacted for acquiring knowledge about or acquisition of the resource'), (b'distributor', 'party who distributes the resource'), (b'user', 'party who uses the resource'), (b'resourceProvider', 'party that supplies the resource'), (b'originator', 'party who created the resource'), (b'owner', 'party that owns the resource'), (b'principalInvestigator', 'key party responsible for gathering information and conducting research')]),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='category',
            field=models.ForeignKey(blank=True, to='base.TopicCategory', help_text='high-level geographic data thematic classification to assist in the grouping and search of available geographic data sets.', null=True),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='featured',
            field=models.BooleanField(default=False, help_text='Should this resource be advertised in home page?'),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='is_published',
            field=models.BooleanField(default=False, help_text='Should this resource be published and searchable?'),
        ),
    ]
