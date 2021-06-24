from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('monitoring', '0013_notifications_def_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationReceiver',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('notification_check', models.ForeignKey(related_name='receivers',
                                                         to='monitoring.NotificationCheck', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='metricnotificationcheck',
            name='user',
        ),
    ]
