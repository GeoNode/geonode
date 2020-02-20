# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '24_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HarvestJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_id', models.CharField(max_length=255)),
                ('status', models.CharField(default='QUEUED', max_length=15, choices=[('QUEUED','QUEUED'), ('IN_PROCESS','IN_PROCESS'), ('PROCESSED','PROCESSED'), ('FAILED','FAILED')])),
                ('service', models.OneToOneField(to='services.Service', on_delete=models.CASCADE)),
            ],
        ),
    ]
