from django.db import migrations, models
from django.utils import timezone
from datetime import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '24_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, max_length=255)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('name_en', models.CharField(max_length=255, unique=True, null=True)),
                ('description', models.TextField(default=None, null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Group Categories',
            },
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='description_en',
            field=models.TextField(null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='title_en',
            field=models.CharField(max_length=50, null=True, verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='categories',
            field=models.ManyToManyField(related_name='groups', to='groups.GroupCategory', blank=True),
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='created',
            field=models.DateTimeField(default=datetime.now(timezone.get_current_timezone()), auto_now_add=True),
            preserve_default=False,
        ),
    ]
