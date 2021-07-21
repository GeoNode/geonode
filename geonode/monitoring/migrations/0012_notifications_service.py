from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0011_notification_def'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metric',
            name='type',
            field=models.CharField(default='rate', max_length=255, choices=[('rate','Rate'), ('count','Count'), ('value','Value'), ('value_numeric','Value numeric')]),
        ),
        migrations.AlterField(
            model_name='metricnotificationcheck',
            name='service',
            field=models.ForeignKey(related_name='checks', blank=True, to='monitoring.Service',
                                    on_delete=models.CASCADE, null=True),
        ),
    ]
