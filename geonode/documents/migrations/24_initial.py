from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('base', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('resourcebase_ptr', models.OneToOneField(parent_link=True, on_delete=models.CASCADE,
                                                          auto_created=True, primary_key=True, serialize=False, to='base.ResourceBase')),
                ('title_en', models.CharField(help_text='name by which the cited resource is known', max_length=255, null=True, verbose_name='title')),
                ('abstract_en', models.TextField(help_text='brief narrative summary of the content of the resource(s)', null=True, verbose_name='abstract', blank=True)),
                ('purpose_en', models.TextField(help_text='summary of the intentions with which the resource(s) was developed', null=True, verbose_name='purpose', blank=True)),
                ('constraints_other_en', models.TextField(help_text='other restrictions and legal prerequisites for accessing and using the resource or metadata', null=True, verbose_name='restrictions other', blank=True)),
                ('supplemental_information_en', models.TextField(default='No information provided', help_text='any other descriptive information about the dataset', null=True, verbose_name='supplemental information')),
                ('data_quality_statement_en', models.TextField(help_text="general explanation of the data producer's knowledge about the lineage of a dataset", null=True, verbose_name='data quality statement', blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('doc_file', models.FileField(max_length=255, upload_to='documents', null=True, verbose_name='File', blank=True)),
                ('extension', models.CharField(max_length=128, null=True, blank=True)),
                ('doc_type', models.CharField(max_length=128, null=True, blank=True)),
                ('doc_url', models.URLField(help_text='The URL of the document if it is external.', max_length=255, null=True, verbose_name='URL', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', on_delete=models.CASCADE, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('base.resourcebase',),
        ),
    ]
