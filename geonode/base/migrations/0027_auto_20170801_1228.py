from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '26_to_27'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='abstract',
            field=models.TextField(help_text='brief narrative summary of the content of the resource(s)', max_length=2000, verbose_name='abstract', blank=True),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='data_quality_statement',
            field=models.TextField(help_text="general explanation of the data producer's knowledge about the lineage of a dataset", max_length=2000, null=True, verbose_name='data quality statement', blank=True),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='purpose',
            field=models.TextField(help_text='summary of the intentions with which the resource(s) was developed', max_length=500, null=True, verbose_name='purpose', blank=True),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='supplemental_information',
            field=models.TextField(default='No information provided', help_text='any other descriptive information about the dataset', max_length=2000, verbose_name='supplemental information'),
        ),
    ]
