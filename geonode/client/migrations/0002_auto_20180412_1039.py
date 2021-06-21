from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geonode_client', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('logo', models.ImageField(null=True, upload_to='img/%Y/%m', blank=True)),
                ('name', models.CharField(max_length=100)),
                ('title', models.CharField(max_length=255)),
                ('href', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Partners',
            },
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='partners_title',
            field=models.CharField(default='Our Partners', max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='partners',
            field=models.ManyToManyField(related_name='partners', to='geonode_client.Partner', blank=True),
        ),
    ]
