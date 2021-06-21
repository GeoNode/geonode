from django.db import migrations, models
from django.utils.timezone import now
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('layers', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('import_id', models.BigIntegerField(null=True)),
                ('state', models.CharField(max_length=16)),
                ('date', models.DateTimeField(default=now, verbose_name='date')),
                ('upload_dir', models.CharField(max_length=100, null=True)),
                ('name', models.CharField(max_length=64, null=True)),
                ('complete', models.BooleanField(default=False)),
                ('session', models.TextField(null=True)),
                ('metadata', models.TextField(null=True)),
                ('mosaic_time_regex', models.CharField(max_length=128, null=True)),
                ('mosaic_time_value', models.CharField(max_length=128, null=True)),
                ('mosaic_elev_regex', models.CharField(max_length=128, null=True)),
                ('mosaic_elev_value', models.CharField(max_length=128, null=True)),
                ('layer', models.ForeignKey(to='layers.Layer', on_delete=models.SET_NULL, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='UploadFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to='uploads')),
                ('slug', models.SlugField(blank=True)),
                ('upload', models.ForeignKey(blank=True, to='upload.Upload', on_delete=models.SET_NULL, null=True)),
            ],
        ),
    ]
