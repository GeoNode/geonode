# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_auto_20160821_1919'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serviceprofilerole',
            name='role',
            field=models.CharField(
                help_text='function performed by the responsible party',
                max_length=255,
                choices=[
                    (b'author', 'party who authored the resource'),
                    (b'processor', 'party who has processed the data in a manner such that the resource has been modified'),
                    (b'publisher', 'party who published the resource'),
                    (b'custodian', 'party that accepts accountability and responsibility for the data and ensures         appropriate care and maintenance of the resource'),
                    (b'pointOfContact', 'party who can be contacted for acquiring knowledge about or acquisition of the resource'),
                    (b'distributor', 'party who distributes the resource'),
                    (b'user', 'party who uses the resource'),
                    (b'resourceProvider', 'party that supplies the resource'),
                    (b'originator', 'party who created the resource'),
                    (b'owner', 'party that owns the resource'),
                    (b'principalInvestigator', 'key party responsible for gathering information and conducting research')]),
        ),
    ]
