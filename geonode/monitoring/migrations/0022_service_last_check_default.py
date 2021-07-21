from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0021_auto_20180301_0932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='last_check',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
