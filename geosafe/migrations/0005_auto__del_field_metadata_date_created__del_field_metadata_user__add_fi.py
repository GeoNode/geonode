# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Metadata.date_created'
        db.delete_column(u'geosafe_metadata', 'date_created')

        # Deleting field 'Metadata.user'
        db.delete_column(u'geosafe_metadata', 'user_id')

        # Adding field 'Metadata.layer_purpose'
        db.add_column(u'geosafe_metadata', 'layer_purpose',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=20, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Metadata.date_created'
        db.add_column(u'geosafe_metadata', 'date_created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow, auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Metadata.user'
        db.add_column(u'geosafe_metadata', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['people.Profile'], null=True, blank=True),
                      keep_default=False)

        # Deleting field 'Metadata.layer_purpose'
        db.delete_column(u'geosafe_metadata', 'layer_purpose')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'base.contactrole': {
            'Meta': {'unique_together': "(('contact', 'resource', 'role'),)", 'object_name': 'ContactRole'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['people.Profile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.ResourceBase']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'base.license': {
            'Meta': {'ordering': "('name',)", 'object_name': 'License'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'license_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'license_text_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'})
        },
        u'base.region': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Region'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['base.Region']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'base.resourcebase': {
            'Meta': {'object_name': 'ResourceBase'},
            'abstract': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bbox_x0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_x1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.TopicCategory']", 'null': 'True', 'blank': 'True'}),
            'constraints_other': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['people.Profile']", 'through': u"orm['base.ContactRole']", 'symmetrical': 'False'}),
            'csw_anytext': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'csw_insert_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'csw_mdsource': ('django.db.models.fields.CharField', [], {'default': "'local'", 'max_length': '256'}),
            'csw_schema': ('django.db.models.fields.CharField', [], {'default': "'http://www.isotc211.org/2005/gmd'", 'max_length': '64'}),
            'csw_type': ('django.db.models.fields.CharField', [], {'default': "'dataset'", 'max_length': '32'}),
            'csw_typename': ('django.db.models.fields.CharField', [], {'default': "'gmd:MD_Metadata'", 'max_length': '32'}),
            'csw_wkt_geometry': ('django.db.models.fields.TextField', [], {'default': "'POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))'"}),
            'data_quality_statement': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_type': ('django.db.models.fields.CharField', [], {'default': "'publication'", 'max_length': '255'}),
            'detail_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'distribution_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'eng'", 'max_length': '3'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.License']", 'null': 'True', 'blank': 'True'}),
            'maintenance_frequency': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'metadata_uploaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'metadata_xml': ('django.db.models.fields.TextField', [], {'default': '\'<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>\'', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_resource'", 'null': 'True', 'to': u"orm['people.Profile']"}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_base.resourcebase_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'popular_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'purpose': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rating': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['base.Region']", 'null': 'True', 'blank': 'True'}),
            'restriction_code_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.RestrictionCodeType']", 'null': 'True', 'blank': 'True'}),
            'share_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'spatial_representation_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.SpatialRepresentationType']", 'null': 'True', 'blank': 'True'}),
            'srid': ('django.db.models.fields.CharField', [], {'default': "'EPSG:4326'", 'max_length': '255'}),
            'supplemental_information': ('django.db.models.fields.TextField', [], {'default': "u'No information provided'"}),
            'temporal_extent_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'temporal_extent_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        u'base.restrictioncodetype': {
            'Meta': {'ordering': "('identifier',)", 'object_name': 'RestrictionCodeType'},
            'description': ('django.db.models.fields.TextField', [], {'max_length': '255'}),
            'description_en': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gn_description': ('django.db.models.fields.TextField', [], {'max_length': '255'}),
            'gn_description_en': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'is_choice': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'base.spatialrepresentationtype': {
            'Meta': {'ordering': "('identifier',)", 'object_name': 'SpatialRepresentationType'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gn_description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gn_description_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'is_choice': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'base.topiccategory': {
            'Meta': {'ordering': "('identifier',)", 'object_name': 'TopicCategory'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'description_en': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'gn_description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True'}),
            'gn_description_en': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'location'", 'max_length': '255'}),
            'is_choice': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'geosafe.analysis': {
            'Meta': {'object_name': 'Analysis'},
            'aggregation_layer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'aggregation_layer'", 'null': 'True', 'to': u"orm['layers.Layer']"}),
            'exposure_layer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exposure_layer'", 'to': u"orm['layers.Layer']"}),
            'extent_option': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'hazard_layer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hazard_layer'", 'to': u"orm['layers.Layer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impact_function_id': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'geosafe.metadata': {
            'Meta': {'object_name': 'Metadata'},
            'layer': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['layers.Layer']", 'unique': 'True', 'primary_key': 'True'}),
            'layer_purpose': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'metadata_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        u'layers.layer': {
            'Meta': {'object_name': 'Layer', '_ormbases': [u'base.ResourceBase']},
            'abstract_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'charset': ('django.db.models.fields.CharField', [], {'default': "'UTF-8'", 'max_length': '255'}),
            'constraints_other_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'data_quality_statement_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'default_style': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'layer_default_style'", 'null': 'True', 'to': u"orm['layers.Style']"}),
            'distribution_description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'purpose_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'resourcebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['base.ResourceBase']", 'unique': 'True', 'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'layer_set'", 'null': 'True', 'to': u"orm['services.Service']"}),
            'store': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'storeType': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'styles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'layer_styles'", 'symmetrical': 'False', 'to': u"orm['layers.Style']"}),
            'supplemental_information_en': ('django.db.models.fields.TextField', [], {'default': "u'No information provided'", 'null': 'True', 'blank': 'True'}),
            'title_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'typename': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'upload_session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['layers.UploadSession']", 'null': 'True', 'blank': 'True'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'layers.style': {
            'Meta': {'object_name': 'Style'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'sld_body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sld_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sld_url': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True'}),
            'sld_version': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'layers.uploadsession': {
            'Meta': {'object_name': 'UploadSession'},
            'context': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'traceback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['people.Profile']"})
        },
        u'people.profile': {
            'Meta': {'object_name': 'Profile'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'delivery': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'profile': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'voice': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'services.service': {
            'Meta': {'object_name': 'Service', '_ormbases': [u'base.ResourceBase']},
            'access_constraints': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'connection_params': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fees': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'first_noanswer': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'noanswer_retries': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'online_resource': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'service_set'", 'null': 'True', 'to': u"orm['services.Service']"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'profiles': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['people.Profile']", 'through': u"orm['services.ServiceProfileRole']", 'symmetrical': 'False'}),
            u'resourcebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['base.ResourceBase']", 'unique': 'True', 'primary_key': 'True'}),
            'resources_ref': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'store_ref': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'workspace_ref': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'services.serviceprofilerole': {
            'Meta': {'object_name': 'ServiceProfileRole'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profiles': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['people.Profile']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['services.Service']"})
        }
    }

    complete_apps = ['geosafe']