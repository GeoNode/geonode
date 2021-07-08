from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('base', '24_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Backup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('description_en', models.TextField(null=True, blank=True)),
                ('base_folder', models.CharField(max_length=100)),
                ('location', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('date',),
                'verbose_name_plural': 'Backups',
            },
        ),
        migrations.CreateModel(
            name='HierarchicalKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=100, verbose_name='Slug')),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaggedContentItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_object', models.ForeignKey(to='base.ResourceBase', on_delete=models.CASCADE)),
                ('tag', models.ForeignKey(related_name='keywords', to='base.HierarchicalKeyword', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Thesaurus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(unique=True, max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('date', models.CharField(default='', max_length=20)),
                ('description', models.TextField(default='', max_length=255)),
                ('slug', models.CharField(default='', max_length=64)),
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Thesauri',
            },
        ),
        migrations.CreateModel(
            name='ThesaurusKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('about', models.CharField(max_length=255, null=True, blank=True)),
                ('alt_label', models.CharField(default='', max_length=255, null=True, blank=True)),
                ('thesaurus', models.ForeignKey(related_name='thesaurus', to='base.Thesaurus', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('alt_label',),
                'verbose_name_plural': 'Thesaurus Keywords',
            },
        ),
        migrations.CreateModel(
            name='ThesaurusKeywordLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lang', models.CharField(max_length=3)),
                ('label', models.CharField(max_length=255)),
                ('keyword', models.ForeignKey(related_name='keyword', to='base.ThesaurusKeyword', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('keyword', 'lang'),
                'verbose_name_plural': 'Labels',
            },
        ),
        migrations.AddField(
            model_name='topiccategory',
            name='fa_class',
            field=models.CharField(default='fa-times', max_length=64),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='keywords',
            field=taggit.managers.TaggableManager(to='base.HierarchicalKeyword', through='base.TaggedContentItem', blank=True, help_text='commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject (space or comma-separated', verbose_name='keywords'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='metadata_uploaded_preserve',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='tkeywords',
            field=models.ManyToManyField(help_text='formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject (space or comma-separated', to='base.ThesaurusKeyword', null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='thesauruskeywordlabel',
            unique_together={('keyword', 'lang')},
        ),
        migrations.AlterUniqueTogether(
            name='thesauruskeyword',
            unique_together={('thesaurus', 'alt_label')},
        ),
    ]
