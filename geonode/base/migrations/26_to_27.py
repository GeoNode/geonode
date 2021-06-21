from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '24_to_26'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='tkeywords',
            field=models.ManyToManyField(help_text='formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject (space or comma-separated', to='base.ThesaurusKeyword', blank=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True, on_delete=models.CASCADE),
        ),

        migrations.AddField(
            model_name='resourcebase',
            name='alternate',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='region',
            name='bbox_x0',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
        migrations.AddField(
            model_name='region',
            name='bbox_x1',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
        migrations.AddField(
            model_name='region',
            name='bbox_y0',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
        migrations.AddField(
            model_name='region',
            name='bbox_y1',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True),
        ),
        migrations.AddField(
            model_name='region',
            name='srid',
            field=models.CharField(default='EPSG:4326', max_length=255),
        ),
    ]
