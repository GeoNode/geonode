from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0005_monitoring_ows_service'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestevent',
            name='request_path',
            field=models.TextField(default=''),
        ),
    ]
