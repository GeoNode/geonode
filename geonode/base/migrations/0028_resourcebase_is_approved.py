from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0027_auto_20170801_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='is_approved',
            field=models.BooleanField(default=False, help_text='Is this resource validated from a publisher or editor?', verbose_name='Approved'),
        ),
    ]
