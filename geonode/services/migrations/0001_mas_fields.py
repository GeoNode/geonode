from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('services', '24_initial')
    ]

    operations = [
        migrations.AddField(
            model_name='Service',
            name='service_refs',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
	    migrations.AddField(
            model_name='Service',
            name='classification',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
	    migrations.AddField(
            model_name='Service',
            name='caveat',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
	    migrations.AddField(
            model_name='Service',
            name='provenance',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ServiceLayer',
            name='category',
            field=models.ForeignKey(blank=True, to='base.TopicCategory', help_text='high-level geographic data thematic classification to assist in the grouping and search of available geographic data sets.', null=True),
        ),
        migrations.AddField(
            model_name='ServiceLayer',
            name='keywords',
			field=models.CharField(max_length=400, blank=True, null=True),
		),
	    migrations.AddField(
            model_name='ServiceLayer',
            name='bbox_x0',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
	    migrations.AddField(
            model_name='ServiceLayer',
            name='bbox_x1',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
	    migrations.AddField(
            model_name='ServiceLayer',
            name='bbox_y0',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
	    migrations.AddField(
            model_name='ServiceLayer',
            name='bbox_y1',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
	    migrations.AddField(
            model_name='ServiceLayer',
            name='srid',
            field=models.CharField(default=b'EPSG:4326', max_length=255, blank=True, null=True),
        )
    ]