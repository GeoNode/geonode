from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0026_auto_20171130_0600'),
    ]

    operations = [
        migrations.AddField(
            model_name='harvestjob',
            name='details',
            field=models.TextField(default='Resource is queued'),
        ),
    ]
