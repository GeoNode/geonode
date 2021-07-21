from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0006_monitoring_path_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='exceptionevent',
            name='error_message',
            field=models.CharField(default='', max_length=255),
        ),
    ]
