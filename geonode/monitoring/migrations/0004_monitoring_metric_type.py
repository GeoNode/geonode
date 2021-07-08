from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0003_monitoring_resources'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='type',
            field=models.CharField(default='rate', max_length=255, choices=[('rate','Rate'), ('count','Count'), ('value','Value')]),
        ),
        migrations.AlterField(
            model_name='exceptionevent',
            name='request',
            field=models.ForeignKey(related_name='exceptions', to='monitoring.RequestEvent', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='metricvalue',
            name='resource',
            field=models.ForeignKey(related_name='metric_values',
                                    to='monitoring.MonitoredResource', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='requestevent',
            name='resources',
            field=models.ManyToManyField(help_text='List of resources affected', related_name='requests', null=True, to='monitoring.MonitoredResource', blank=True),
        ),
        migrations.AlterField(
            model_name='servicetypemetric',
            name='metric',
            field=models.ForeignKey(related_name='service_type', to='monitoring.Metric', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='servicetypemetric',
            name='service_type',
            field=models.ForeignKey(related_name='metric', to='monitoring.ServiceType', on_delete=models.CASCADE),
        ),
    ]
