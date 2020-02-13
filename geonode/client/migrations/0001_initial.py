# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GeoNodeThemeCustomization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('is_enabled', models.BooleanField(default=False)),
                ('logo', models.ImageField(null=True, upload_to='img/%Y/%m', blank=True)),
                ('jumbotron_bg', models.ImageField(null=True, upload_to='img/%Y/%m', blank=True)),
                ('body_color', models.CharField(default='#333333', max_length=10)),
                ('navbar_color', models.CharField(default='#333333', max_length=10)),
                ('jumbotron_color', models.CharField(default='#2c689c', max_length=10)),
                ('copyright_color', models.CharField(default='#2c689c', max_length=10)),
                ('contactus', models.BooleanField(default=False)),
                ('copyright', models.TextField(null=True, blank=True)),
                ('contact_name', models.TextField(null=True, blank=True)),
                ('contact_position', models.TextField(null=True, blank=True)),
                ('contact_administrative_area', models.TextField(null=True, blank=True)),
                ('contact_street', models.TextField(null=True, blank=True)),
                ('contact_postal_code', models.TextField(null=True, blank=True)),
                ('contact_city', models.TextField(null=True, blank=True)),
                ('contact_country', models.TextField(null=True, blank=True)),
                ('contact_delivery_point', models.TextField(null=True, blank=True)),
                ('contact_voice', models.TextField(null=True, blank=True)),
                ('contact_facsimile', models.TextField(null=True, blank=True)),
                ('contact_email', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('date',),
                'verbose_name_plural': 'Themes',
            },
        ),
    ]
