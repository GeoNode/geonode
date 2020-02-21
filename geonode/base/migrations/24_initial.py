# -*- coding: utf-8 -*-


from django.db import migrations, models
import mptt.fields
import geonode.security.models
from django.conf import settings
from django.utils.timezone import now


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(help_text='function performed by the responsible party', max_length=255, choices=[('author', 'party who authored the resource'), ('processor', 'party who has processed the data in a manner such that the resource has been modified'), ('publisher', 'party who published the resource'), ('custodian', 'party that accepts accountability and responsibility for the data and ensures         appropriate care and maintenance of the resource'), ('pointOfContact', 'party who can be contacted for acquiring knowledge about or acquisition of the resource'), ('distributor', 'party who distributes the resource'), ('user', 'party who uses the resource'), ('resourceProvider', 'party that supplies the resource'), ('originator', 'party who created the resource'), ('owner', 'party that owns the resource'), ('principalInvestigator', 'key party responsible for gathering information and conducting research')])),
                ('contact', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100, null=True)),
                ('abbreviation', models.CharField(max_length=20, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('description_en', models.TextField(null=True, blank=True)),
                ('url', models.URLField(max_length=2000, null=True, blank=True)),
                ('license_text', models.TextField(null=True, blank=True)),
                ('license_text_en', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Licenses',
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extension', models.CharField(help_text='For example "kml"', max_length=255)),
                ('link_type', models.CharField(max_length=255, choices=[('original','original'), ('data','data'), ('image','image'), ('metadata','metadata'), ('html','html'), ('OGC:WMS','OGC:WMS'), ('OGC:WFS','OGC:WFS'), ('OGC:WCS','OGC:WCS')])),
                ('name', models.CharField(help_text='For example "View in Google Earth"', max_length=255)),
                ('mime', models.CharField(help_text='For example "text/xml"', max_length=255)),
                ('url', models.TextField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=50)),
                ('name', models.CharField(max_length=255)),
                ('name_en', models.CharField(max_length=255, null=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children',
                                                      on_delete=models.CASCADE, blank=True, to='base.Region', null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Metadata Regions',
            },
        ),
        migrations.CreateModel(
            name='ResourceBase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36)),
                ('title', models.CharField(help_text='name by which the cited resource is known', max_length=255, verbose_name='title')),
                ('date', models.DateTimeField(default=now, help_text='reference date for the cited resource', verbose_name='date')),
                ('date_type', models.CharField(default='publication', help_text='identification of when a given event occurred', max_length=255, verbose_name='date type', choices=[('creation', 'Creation'), ('publication', 'Publication'), ('revision', 'Revision')])),
                ('edition', models.CharField(help_text='version of the cited resource', max_length=255, null=True, verbose_name='edition', blank=True)),
                ('abstract', models.TextField(help_text='brief narrative summary of the content of the resource(s)', verbose_name='abstract', blank=True)),
                ('purpose', models.TextField(help_text='summary of the intentions with which the resource(s) was developed', null=True, verbose_name='purpose', blank=True)),
                ('maintenance_frequency', models.CharField(choices=[('unknown', 'frequency of maintenance for the data is not known'), ('continual', 'data is repeatedly and frequently updated'), ('notPlanned', 'there are no plans to update the data'), ('daily', 'data is updated each day'), ('annually', 'data is updated every year'), ('asNeeded', 'data is updated as deemed necessary'), ('monthly', 'data is updated each month'), ('fortnightly', 'data is updated every two weeks'), ('irregular', 'data is updated in intervals that are uneven in duration'), ('weekly', 'data is updated on a weekly basis'), ('biannually', 'data is updated twice each year'), ('quarterly', 'data is updated every three months')], max_length=255, blank=True, help_text='frequency with which modifications and deletions are made to the data after it is first produced', null=True, verbose_name='maintenance frequency')),
                ('constraints_other', models.TextField(help_text='other restrictions and legal prerequisites for accessing and using the resource or metadata', null=True, verbose_name='restrictions other', blank=True)),
                ('language', models.CharField(default='eng', help_text='language used within the dataset', max_length=3, verbose_name='language', choices=[('abk','Abkhazian'), ('aar','Afar'), ('afr','Afrikaans'), ('amh','Amharic'), ('ara','Arabic'), ('asm','Assamese'), ('aym','Aymara'), ('aze','Azerbaijani'), ('bak','Bashkir'), ('ben','Bengali'), ('bih','Bihari'), ('bis','Bislama'), ('bre','Breton'), ('bul','Bulgarian'), ('bel','Byelorussian'), ('cat','Catalan'), ('cos','Corsican'), ('dan','Danish'), ('dzo','Dzongkha'), ('eng','English'), ('fra','French'), ('epo','Esperanto'), ('est','Estonian'), ('fao','Faroese'), ('fij','Fijian'), ('fin','Finnish'), ('fry','Frisian'), ('glg','Gallegan'), ('ger','German'), ('kal','Greenlandic'), ('grn','Guarani'), ('guj','Gujarati'), ('hau','Hausa'), ('heb','Hebrew'), ('hin','Hindi'), ('hun','Hungarian'), ('ind','Indonesian'), ('ina','Interlingua (International Auxiliary language Association)'), ('iku','Inuktitut'), ('ipk','Inupiak'), ('ita','Italian'), ('jpn','Japanese'), ('kan','Kannada'), ('kas','Kashmiri'), ('kaz','Kazakh'), ('khm','Khmer'), ('kin','Kinyarwanda'), ('kir','Kirghiz'), ('kor','Korean'), ('kur','Kurdish'), ('oci', b"Langue d 'Oc (post 1500)"), ('lao','Lao'), ('lat','Latin'), ('lav','Latvian'), ('lin','Lingala'), ('lit','Lithuanian'), ('mlg','Malagasy'), ('mlt','Maltese'), ('mar','Marathi'), ('mol','Moldavian'), ('mon','Mongolian'), ('nau','Nauru'), ('nep','Nepali'), ('nor','Norwegian'), ('ori','Oriya'), ('orm','Oromo'), ('pan','Panjabi'), ('pol','Polish'), ('por','Portuguese'), ('pus','Pushto'), ('que','Quechua'), ('roh','Rhaeto-Romance'), ('run','Rundi'), ('rus','Russian'), ('smo','Samoan'), ('sag','Sango'), ('san','Sanskrit'), ('scr','Serbo-Croatian'), ('sna','Shona'), ('snd','Sindhi'), ('sin','Singhalese'), ('ssw','Siswant'), ('slv','Slovenian'), ('som','Somali'), ('sot','Sotho'), ('spa','Spanish'), ('sun','Sudanese'), ('swa','Swahili'), ('tgl','Tagalog'), ('tgk','Tajik'), ('tam','Tamil'), ('tat','Tatar'), ('tel','Telugu'), ('tha','Thai'), ('tir','Tigrinya'), ('tog','Tonga (Nyasa)'), ('tso','Tsonga'), ('tsn','Tswana'), ('tur','Turkish'), ('tuk','Turkmen'), ('twi','Twi'), ('uig','Uighur'), ('ukr','Ukrainian'), ('urd','Urdu'), ('uzb','Uzbek'), ('vie','Vietnamese'), ('vol','Volap\xc3\xbck'), ('wol','Wolof'), ('xho','Xhosa'), ('yid','Yiddish'), ('yor','Yoruba'), ('zha','Zhuang'), ('zul','Zulu')])),
                ('temporal_extent_start', models.DateTimeField(help_text='time period covered by the content of the dataset (start)', null=True, verbose_name='temporal extent start', blank=True)),
                ('temporal_extent_end', models.DateTimeField(help_text='time period covered by the content of the dataset (end)', null=True, verbose_name='temporal extent end', blank=True)),
                ('supplemental_information', models.TextField(default='No information provided', help_text='any other descriptive information about the dataset', verbose_name='supplemental information')),
                ('data_quality_statement', models.TextField(help_text="general explanation of the data producer's knowledge about the lineage of a dataset", null=True, verbose_name='data quality statement', blank=True)),
                ('bbox_x0', models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True)),
                ('bbox_x1', models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True)),
                ('bbox_y0', models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True)),
                ('bbox_y1', models.DecimalField(null=True, max_digits=19, decimal_places=10, blank=True)),
                ('srid', models.CharField(default='EPSG:4326', max_length=255)),
                ('csw_typename', models.CharField(default='gmd:MD_Metadata', max_length=32, verbose_name='CSW typename')),
                ('csw_schema', models.CharField(default='http://www.isotc211.org/2005/gmd', max_length=64, verbose_name='CSW schema')),
                ('csw_mdsource', models.CharField(default='local', max_length=256, verbose_name='CSW source')),
                ('csw_insert_date', models.DateTimeField(auto_now_add=True, verbose_name='CSW insert date', null=True)),
                ('csw_type', models.CharField(default='dataset', max_length=32, verbose_name='CSW type', choices=[('series', 'series'), ('software', 'computer program or routine'), ('featureType', 'feature type'), ('model', 'copy or imitation of an existing or hypothetical object'), ('collectionHardware', 'collection hardware'), ('collectionSession', 'collection session'), ('nonGeographicDataset', 'non-geographic data'), ('propertyType', 'property type'), ('fieldSession', 'field session'), ('dataset', 'dataset'), ('service', 'service interfaces'), ('attribute', 'attribute class'), ('attributeType', 'characteristic of a feature'), ('tile', 'tile or spatial subset of geographic data'), ('feature', 'feature'), ('dimensionGroup', 'dimension group')])),
                ('csw_anytext', models.TextField(null=True, verbose_name='CSW anytext', blank=True)),
                ('csw_wkt_geometry', models.TextField(default='POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))', verbose_name='CSW WKT geometry')),
                ('metadata_uploaded', models.BooleanField(default=False)),
                ('metadata_xml', models.TextField(default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>', null=True, blank=True)),
                ('popular_count', models.IntegerField(default=0)),
                ('share_count', models.IntegerField(default=0)),
                ('featured', models.BooleanField(default=False, help_text='Should this resource be advertised in home page?', verbose_name='Featured')),
                ('is_published', models.BooleanField(default=True, help_text='Should this resource be published and searchable?', verbose_name='Is Published')),
                ('thumbnail_url', models.TextField(null=True, blank=True)),
                ('detail_url', models.CharField(max_length=255, null=True, blank=True)),
                ('rating', models.IntegerField(default=0, null=True, blank=True)),
            ],
            options={
                'permissions': (('view_resourcebase', 'Can view resource'), ('change_resourcebase_permissions', 'Can change resource permissions'), ('download_resourcebase', 'Can download resource'), ('publish_resourcebase', 'Can publish resource'), ('change_resourcebase_metadata', 'Can change resource metadata')),
            },
            bases=(geonode.security.models.PermissionLevelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='RestrictionCodeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('description', models.TextField(max_length=255, editable=False)),
                ('description_en', models.TextField(max_length=255, null=True, editable=False)),
                ('gn_description', models.TextField(max_length=255, verbose_name='GeoNode description')),
                ('gn_description_en', models.TextField(max_length=255, null=True, verbose_name='GeoNode description')),
                ('is_choice', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Metadata Restriction Code Types',
            },
        ),
        migrations.CreateModel(
            name='SpatialRepresentationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('description', models.CharField(max_length=255, editable=False)),
                ('description_en', models.CharField(max_length=255, null=True, editable=False)),
                ('gn_description', models.CharField(max_length=255, verbose_name='GeoNode description')),
                ('gn_description_en', models.CharField(max_length=255, null=True, verbose_name='GeoNode description')),
                ('is_choice', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Metadata Spatial Representation Types',
            },
        ),
        migrations.CreateModel(
            name='TopicCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(default='location', max_length=255)),
                ('description', models.TextField(default='')),
                ('description_en', models.TextField(default='', null=True)),
                ('gn_description', models.TextField(default='', null=True, verbose_name='GeoNode description')),
                ('gn_description_en', models.TextField(default='', null=True, verbose_name='GeoNode description')),
                ('is_choice', models.BooleanField(default=True))
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Metadata Topic Categories',
            },
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='category',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='base.TopicCategory',
                                    help_text='high-level geographic data thematic classification to assist in the grouping and search of available geographic data sets.', null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='contacts',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='base.ContactRole'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='license',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='base.License',
                                    help_text='license of the dataset', null=True, verbose_name='License'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='owner',
            field=models.ForeignKey(related_name='owned_resource', on_delete=models.CASCADE,
                                    verbose_name='Owner', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_base.resourcebase_set+',
                                    on_delete=models.CASCADE, editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='regions',
            field=models.ManyToManyField(help_text='keyword identifies a location', to='base.Region', verbose_name='keywords region', blank=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='restriction_code_type',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='base.RestrictionCodeType',
                                    help_text='limitation(s) placed upon the access or use of the data.', null=True, verbose_name='restrictions'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='spatial_representation_type',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='base.SpatialRepresentationType',
                                    help_text='method used to represent geographic information in the dataset.', null=True, verbose_name='spatial representation type'),
        ),
        migrations.AddField(
            model_name='link',
            name='resource',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='base.ResourceBase', null=True),
        ),
        migrations.AddField(
            model_name='contactrole',
            name='resource',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='base.ResourceBase', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='contactrole',
            unique_together=set([('contact', 'resource', 'role')]),
        ),
    ]
