# Generated by Django 3.2.18 on 2023-03-31 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0094_auto_20230331_0918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='date_accepted',
            field=models.DateField(blank=True, help_text='The date that the publisher accepted the resource into their system.', null=True, verbose_name='date accepted'),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='date_collected',
            field=models.DateField(blank=True, help_text='The date or date range in which the dataset content was collected', null=True, verbose_name='date collected'),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='date_copyrighted',
            field=models.DateField(blank=True, help_text='The specific, documented date at which the dataset receives a copyrighted status, if applicable.', null=True, verbose_name='date copyrighted'),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='date_issued',
            field=models.DateField(blank=True, help_text='The date that the resource is published or distributed e.g. to a data centre.', null=True, verbose_name='date issued'),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='date_submitted',
            field=models.DateField(blank=True, help_text='The date the creator submits the resource to the publisher. This could be different from Accepted if the publisher the applies a selection process. To indicate the start of an embargo period. ', null=True, verbose_name='date submitted'),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='date_valid',
            field=models.DateField(blank=True, help_text='The date or date range during which the dataset or resource is accurate.', null=True, verbose_name='date valid'),
        ),
    ]