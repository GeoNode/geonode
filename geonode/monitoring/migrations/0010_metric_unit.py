from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0009_sample_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='unit',
            field=models.CharField(blank=True, max_length=255, null=True, choices=[('B','Bytes'), ('MB','Megabytes'), ('GB','Gigabytes'), ('B/s','Bytes per second'), ('MB/s','Megabytes per second'), ('GB/s','Gigabytes per second'), ('s','Seconds'), ('Rate','Rate'), ('%','Percentage'), ('Count','Count')]),
        ),
        migrations.AlterField(
            model_name='metricvalue',
            name='ows_service',
            field=models.ForeignKey(related_name='metric_values', blank=True,
                                    to='monitoring.OWSService', on_delete=models.CASCADE, null=True),
        ),
        migrations.AlterField(
            model_name='owsservice',
            name='name',
            field=models.CharField(unique=True, max_length=16, choices=[('TMS','TMS'), ('WMS-C','WMS-C'), ('WMTS','WMTS'), ('WCS','WCS'), ('WFS','WFS'), ('WMS','WMS'), ('WPS','WPS'), ('all','All'), ('other','Other')]),
        ),
    ]
