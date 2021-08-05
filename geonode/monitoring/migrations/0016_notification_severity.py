from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0015_notification_grace_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationcheck',
            name='severity',
            field=models.CharField(default='error', max_length=32, choices=[('warning','Warning'), ('error','Error'), ('fatal','Fatal')]),
        ),
    ]
