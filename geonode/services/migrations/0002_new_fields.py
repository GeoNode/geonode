from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('services', '0001_mas_fields')
    ]

    operations = [
        migrations.AddField(
            model_name='ServiceLayer',
            name='uuid',
            field=models.CharField(max_length=36, blank=True, null=True),
        )
    ]