# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Map.csw_mdsource'
        db.delete_column('maps_map', 'csw_mdsource')

        # Deleting field 'Map.csw_schema'
        db.delete_column('maps_map', 'csw_schema')

        # Deleting field 'Map.csw_typename'
        db.delete_column('maps_map', 'csw_typename')

        # Deleting field 'Map.constraints_other'
        db.delete_column('maps_map', 'constraints_other')

        # Deleting field 'Map.date'
        db.delete_column('maps_map', 'date')

        # Deleting field 'Map.owner'
        db.delete_column('maps_map', 'owner_id')

        # Deleting field 'Map.uuid'
        db.delete_column('maps_map', 'uuid')

        # Deleting field 'Map.title'
        db.delete_column('maps_map', 'title')

        # Deleting field 'Map.date_type'
        db.delete_column('maps_map', 'date_type')

        # Deleting field 'Map.csw_insert_date'
        db.delete_column('maps_map', 'csw_insert_date')

        # Deleting field 'Map.temporal_extent_end'
        db.delete_column('maps_map', 'temporal_extent_end')

        # Deleting field 'Map.distribution_url'
        db.delete_column('maps_map', 'distribution_url')

        # Deleting field 'Map.data_quality_statement'
        db.delete_column('maps_map', 'data_quality_statement')

        # Deleting field 'Map.metadata_xml'
        db.delete_column('maps_map', 'metadata_xml')

        # Deleting field 'Map.temporal_extent_start'
        db.delete_column('maps_map', 'temporal_extent_start')

        # Deleting field 'Map.bbox_x1'
        db.delete_column('maps_map', 'bbox_x1')

        # Deleting field 'Map.bbox_x0'
        db.delete_column('maps_map', 'bbox_x0')

        # Deleting field 'Map.distribution_description'
        db.delete_column('maps_map', 'distribution_description')

        # Deleting field 'Map.abstract'
        db.delete_column('maps_map', 'abstract')

        # Deleting field 'Map.supplemental_information'
        db.delete_column('maps_map', 'supplemental_information')

        # Deleting field 'Map.edition'
        db.delete_column('maps_map', 'edition')

        # Deleting field 'Map.id'
        db.delete_column('maps_map', 'id')

        # Deleting field 'Map.category'
        db.delete_column('maps_map', 'category_id')

        # Deleting field 'Map.spatial_representation_type'
        db.delete_column('maps_map', 'spatial_representation_type')

        # Deleting field 'Map.maintenance_frequency'
        db.delete_column('maps_map', 'maintenance_frequency')

        # Deleting field 'Map.bbox_y0'
        db.delete_column('maps_map', 'bbox_y0')

        # Deleting field 'Map.bbox_y1'
        db.delete_column('maps_map', 'bbox_y1')

        # Deleting field 'Map.topic_category'
        db.delete_column('maps_map', 'topic_category')

        # Deleting field 'Map.purpose'
        db.delete_column('maps_map', 'purpose')

        # Deleting field 'Map.srid'
        db.delete_column('maps_map', 'srid')

        # Deleting field 'Map.language'
        db.delete_column('maps_map', 'language')

        # Deleting field 'Map.keywords_region'
        db.delete_column('maps_map', 'keywords_region')

        # Deleting field 'Map.csw_anytext'
        db.delete_column('maps_map', 'csw_anytext')

        # Deleting field 'Map.csw_type'
        db.delete_column('maps_map', 'csw_type')

        # Deleting field 'Map.metadata_uploaded'
        db.delete_column('maps_map', 'metadata_uploaded')

        # Deleting field 'Map.csw_wkt_geometry'
        db.delete_column('maps_map', 'csw_wkt_geometry')

        # Deleting field 'Map.constraints_use'
        db.delete_column('maps_map', 'constraints_use')

        # Adding field 'Map.resourcebase_ptr'
        db.add_column('maps_map', 'resourcebase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(default=0, to=orm['base.ResourceBase'], unique=True, primary_key=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'Map.csw_mdsource'
        db.add_column('maps_map', 'csw_mdsource', self.gf('django.db.models.fields.CharField')(default='local', max_length=256), keep_default=False)

        # Adding field 'Map.csw_schema'
        db.add_column('maps_map', 'csw_schema', self.gf('django.db.models.fields.CharField')(default='http://www.isotc211.org/2005/gmd', max_length=64), keep_default=False)

        # Adding field 'Map.csw_typename'
        db.add_column('maps_map', 'csw_typename', self.gf('django.db.models.fields.CharField')(default='gmd:MD_Metadata', max_length=32), keep_default=False)

        # Adding field 'Map.constraints_other'
        db.add_column('maps_map', 'constraints_other', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.date'
        db.add_column('maps_map', 'date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now), keep_default=False)

        # Adding field 'Map.owner'
        db.add_column('maps_map', 'owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True), keep_default=False)

        # Adding field 'Map.uuid'
        db.add_column('maps_map', 'uuid', self.gf('django.db.models.fields.CharField')(default=0, max_length=36), keep_default=False)

        # Adding field 'Map.title'
        db.add_column('maps_map', 'title', self.gf('django.db.models.fields.CharField')(default='', max_length=255), keep_default=False)

        # Adding field 'Map.date_type'
        db.add_column('maps_map', 'date_type', self.gf('django.db.models.fields.CharField')(default='publication', max_length=255), keep_default=False)

        # Adding field 'Map.csw_insert_date'
        db.add_column('maps_map', 'csw_insert_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True), keep_default=False)

        # Adding field 'Map.temporal_extent_end'
        db.add_column('maps_map', 'temporal_extent_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.distribution_url'
        db.add_column('maps_map', 'distribution_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.data_quality_statement'
        db.add_column('maps_map', 'data_quality_statement', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.metadata_xml'
        db.add_column('maps_map', 'metadata_xml', self.gf('django.db.models.fields.TextField')(default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>', null=True, blank=True), keep_default=False)

        # Adding field 'Map.temporal_extent_start'
        db.add_column('maps_map', 'temporal_extent_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.bbox_x1'
        db.add_column('maps_map', 'bbox_x1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Map.bbox_x0'
        db.add_column('maps_map', 'bbox_x0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Map.distribution_description'
        db.add_column('maps_map', 'distribution_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.abstract'
        db.add_column('maps_map', 'abstract', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Map.supplemental_information'
        db.add_column('maps_map', 'supplemental_information', self.gf('django.db.models.fields.TextField')(default=u'No information provided'), keep_default=False)

        # Adding field 'Map.edition'
        db.add_column('maps_map', 'edition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Map.id'
        db.add_column('maps_map', 'id', self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True), keep_default=False)

        # Adding field 'Map.category'
        db.add_column('maps_map', 'category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.TopicCategory'], null=True, blank=True), keep_default=False)

        # Adding field 'Map.spatial_representation_type'
        db.add_column('maps_map', 'spatial_representation_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Map.maintenance_frequency'
        db.add_column('maps_map', 'maintenance_frequency', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Map.bbox_y0'
        db.add_column('maps_map', 'bbox_y0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Map.bbox_y1'
        db.add_column('maps_map', 'bbox_y1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Map.topic_category'
        db.add_column('maps_map', 'topic_category', self.gf('django.db.models.fields.CharField')(default='location', max_length=255), keep_default=False)

        # Adding field 'Map.purpose'
        db.add_column('maps_map', 'purpose', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.srid'
        db.add_column('maps_map', 'srid', self.gf('django.db.models.fields.CharField')(default='EPSG:4326', max_length=255), keep_default=False)

        # Adding field 'Map.language'
        db.add_column('maps_map', 'language', self.gf('django.db.models.fields.CharField')(default='eng', max_length=3), keep_default=False)

        # Adding field 'Map.keywords_region'
        db.add_column('maps_map', 'keywords_region', self.gf('django.db.models.fields.CharField')(default='USA', max_length=3), keep_default=False)

        # Adding field 'Map.csw_anytext'
        db.add_column('maps_map', 'csw_anytext', self.gf('django.db.models.fields.TextField')(null=True), keep_default=False)

        # Adding field 'Map.csw_type'
        db.add_column('maps_map', 'csw_type', self.gf('django.db.models.fields.CharField')(default='dataset', max_length=32), keep_default=False)

        # Adding field 'Map.metadata_uploaded'
        db.add_column('maps_map', 'metadata_uploaded', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Map.csw_wkt_geometry'
        db.add_column('maps_map', 'csw_wkt_geometry', self.gf('django.db.models.fields.TextField')(default='SRID=4326;POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))'), keep_default=False)

        # Adding field 'Map.constraints_use'
        db.add_column('maps_map', 'constraints_use', self.gf('django.db.models.fields.CharField')(default='copyright', max_length=255), keep_default=False)

        # Deleting field 'Map.resourcebase_ptr'
        db.delete_column('maps_map', 'resourcebase_ptr_id')


    models = {
        'actstream.action': {
            'Meta': {'ordering': "('-timestamp',)", 'object_name': 'Action'},
            'action_object_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'action_object'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'action_object_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'actor_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actor'", 'to': "orm['contenttypes.ContentType']"}),
            'actor_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'data': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'target_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'target'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'target_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 15, 3, 5, 12, 100963)'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 15, 3, 5, 12, 107271)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 15, 3, 5, 12, 107211)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'relationships': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_to'", 'symmetrical': 'False', 'through': "orm['relationships.Relationship']", 'to': "orm['auth.User']"}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'base.contactrole': {
            'Meta': {'unique_together': "(('contact', 'resource', 'role'),)", 'object_name': 'ContactRole'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Profile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.ResourceBase']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Role']"})
        },
        'base.resourcebase': {
            'Meta': {'object_name': 'ResourceBase'},
            'abstract': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bbox_x0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_x1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.TopicCategory']", 'null': 'True', 'blank': 'True'}),
            'constraints_other': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'constraints_use': ('django.db.models.fields.CharField', [], {'default': "'copyright'", 'max_length': '255'}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['people.Profile']", 'through': "orm['base.ContactRole']", 'symmetrical': 'False'}),
            'csw_anytext': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'csw_insert_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'csw_mdsource': ('django.db.models.fields.CharField', [], {'default': "'local'", 'max_length': '256'}),
            'csw_schema': ('django.db.models.fields.CharField', [], {'default': "'http://www.isotc211.org/2005/gmd'", 'max_length': '64'}),
            'csw_type': ('django.db.models.fields.CharField', [], {'default': "'dataset'", 'max_length': '32'}),
            'csw_typename': ('django.db.models.fields.CharField', [], {'default': "'gmd:MD_Metadata'", 'max_length': '32'}),
            'csw_wkt_geometry': ('django.db.models.fields.TextField', [], {'default': "'SRID=4326;POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))'"}),
            'data_quality_statement': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_type': ('django.db.models.fields.CharField', [], {'default': "'publication'", 'max_length': '255'}),
            'distribution_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords_region': ('django.db.models.fields.CharField', [], {'default': "'USA'", 'max_length': '3'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'eng'", 'max_length': '3'}),
            'maintenance_frequency': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'metadata_uploaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'metadata_xml': ('django.db.models.fields.TextField', [], {'default': '\'<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>\'', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'purpose': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'spatial_representation_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'srid': ('django.db.models.fields.CharField', [], {'default': "'EPSG:4326'", 'max_length': '255'}),
            'supplemental_information': ('django.db.models.fields.TextField', [], {'default': "u'No information provided'"}),
            'temporal_extent_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'temporal_extent_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Thumbnail']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        'base.thumbnail': {
            'Meta': {'object_name': 'Thumbnail'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thumb_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'thumb_spec': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True'})
        },
        'base.topiccategory': {
            'Meta': {'ordering': "('name',)", 'object_name': 'TopicCategory'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'maps.map': {
            'Meta': {'object_name': 'Map', '_ormbases': ['base.ResourceBase']},
            'center_x': ('django.db.models.fields.FloatField', [], {}),
            'center_y': ('django.db.models.fields.FloatField', [], {}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'popular_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'projection': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'resourcebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.ResourceBase']", 'unique': 'True', 'primary_key': 'True'}),
            'share_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'zoom': ('django.db.models.fields.IntegerField', [], {})
        },
        'maps.maplayer': {
            'Meta': {'ordering': "['stack_order']", 'object_name': 'MapLayer'},
            'fixed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer_params': ('django.db.models.fields.TextField', [], {}),
            'local': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'layer_set'", 'to': "orm['maps.Map']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'opacity': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'ows_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'source_params': ('django.db.models.fields.TextField', [], {}),
            'stack_order': ('django.db.models.fields.IntegerField', [], {}),
            'styles': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'transparent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'visibility': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'people.profile': {
            'Meta': {'object_name': 'Profile'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'delivery': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'profile': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'profile'", 'unique': 'True', 'null': 'True', 'to': "orm['auth.User']"}),
            'voice': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'people.role': {
            'Meta': {'object_name': 'Role'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'relationships.relationship': {
            'Meta': {'ordering': "('created',)", 'unique_together': "(('from_user', 'to_user', 'status', 'site'),)", 'object_name': 'Relationship'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'relationships'", 'to': "orm['sites.Site']"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['relationships.RelationshipStatus']"}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"}),
            'weight': ('django.db.models.fields.FloatField', [], {'default': '1.0', 'null': 'True', 'blank': 'True'})
        },
        'relationships.relationshipstatus': {
            'Meta': {'ordering': "('name',)", 'object_name': 'RelationshipStatus'},
            'from_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'symmetrical_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'to_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['maps']
