from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '26_to_27'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='groupinvitation',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='groupinvitation',
            name='from_user',
        ),
        migrations.RemoveField(
            model_name='groupinvitation',
            name='group',
        ),
        migrations.RemoveField(
            model_name='groupinvitation',
            name='user',
        ),
        migrations.DeleteModel(
            name='GroupInvitation',
        ),
    ]
