from django.db import migrations, models
from django.db.models.fields.json import JSONField


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0018_notification_check_def'),
    ]

    operations = [
        migrations.AddField(
            model_name='metricnotificationcheck',
            name='definition',
            field=models.OneToOneField(related_name='metric_check', on_delete=models.CASCADE,
                                       null=True, to='monitoring.NotificationMetricDefinition'),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='active',
            field=models.BooleanField(default=True, help_text='Is it active'),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='description',
            field=models.CharField(help_text='Description of the alert', max_length=255),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='severity',
            field=models.CharField(default='error', help_text='How severe would be error from this notification', max_length=32, choices=[('warning','Warning'), ('error','Error'), ('fatal','Fatal')]),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='user_threshold',
            field=JSONField(default=dict, help_text='Expected min/max values for user configuration'),
        ),
    ]
