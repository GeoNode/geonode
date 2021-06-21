from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0031_auto_20180309_0837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='is_approved',
            field=models.BooleanField(default=True, help_text='Is this resource validated from a publisher or editor?', verbose_name='Approved'),
        ),
    ]
