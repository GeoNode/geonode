from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0029_auto_20171203_1624'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='webserviceharvestlayersjob',
            name='service',
        ),
        migrations.DeleteModel(
            name='WebServiceRegistrationJob',
        ),
        migrations.AlterField(
            model_name='harvestjob',
            name='status',
            field=models.CharField(default='QUEUED', max_length=15, choices=[('QUEUED','QUEUED'), ('CANCELLED','QUEUED'), ('IN_PROCESS','IN_PROCESS'), ('PROCESSED','PROCESSED'), ('FAILED','FAILED')]),
        ),
        migrations.DeleteModel(
            name='WebServiceHarvestLayersJob',
        ),
    ]
