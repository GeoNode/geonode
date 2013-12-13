# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'ContactRole', fields ['contact', 'layer', 'role']
        db.delete_unique('layers_contactrole', ['contact_id', 'layer_id', 'role_id'])

        # Deleting model 'Link'
        db.delete_table('layers_link')

        # Deleting model 'TopicCategory'
        db.delete_table('layers_topiccategory')

        # Deleting model 'ContactRole'
        db.delete_table('layers_contactrole')

        # Deleting field 'Layer.csw_mdsource'
        db.delete_column('layers_layer', 'csw_mdsource')

        # Deleting field 'Layer.csw_schema'
        db.delete_column('layers_layer', 'csw_schema')

        # Deleting field 'Layer.csw_typename'
        db.delete_column('layers_layer', 'csw_typename')

        # Deleting field 'Layer.constraints_other'
        db.delete_column('layers_layer', 'constraints_other')

        # Deleting field 'Layer.date'
        db.delete_column('layers_layer', 'date')

        # Deleting field 'Layer.owner'
        db.delete_column('layers_layer', 'owner_id')

        # Deleting field 'Layer.uuid'
        db.delete_column('layers_layer', 'uuid')

        # Deleting field 'Layer.title'
        db.delete_column('layers_layer', 'title')

        # Deleting field 'Layer.date_type'
        db.delete_column('layers_layer', 'date_type')

        # Deleting field 'Layer.csw_insert_date'
        db.delete_column('layers_layer', 'csw_insert_date')

        # Deleting field 'Layer.temporal_extent_end'
        db.delete_column('layers_layer', 'temporal_extent_end')

        # Deleting field 'Layer.distribution_url'
        db.delete_column('layers_layer', 'distribution_url')

        # Deleting field 'Layer.metadata_xml'
        db.delete_column('layers_layer', 'metadata_xml')

        # Deleting field 'Layer.data_quality_statement'
        db.delete_column('layers_layer', 'data_quality_statement')

        # Deleting field 'Layer.temporal_extent_start'
        db.delete_column('layers_layer', 'temporal_extent_start')

        # Deleting field 'Layer.bbox_x1'
        db.delete_column('layers_layer', 'bbox_x1')

        # Deleting field 'Layer.bbox_x0'
        db.delete_column('layers_layer', 'bbox_x0')

        # Deleting field 'Layer.distribution_description'
        db.delete_column('layers_layer', 'distribution_description')

        # Deleting field 'Layer.abstract'
        db.delete_column('layers_layer', 'abstract')

        # Deleting field 'Layer.supplemental_information'
        db.delete_column('layers_layer', 'supplemental_information')

        # Deleting field 'Layer.edition'
        db.delete_column('layers_layer', 'edition')

        # Deleting field 'Layer.id'
        db.delete_column('layers_layer', 'id')

        # Deleting field 'Layer.category'
        db.delete_column('layers_layer', 'category_id')

        # Deleting field 'Layer.spatial_representation_type'
        db.delete_column('layers_layer', 'spatial_representation_type')

        # Deleting field 'Layer.bbox_y0'
        db.delete_column('layers_layer', 'bbox_y0')

        # Deleting field 'Layer.bbox_y1'
        db.delete_column('layers_layer', 'bbox_y1')

        # Deleting field 'Layer.topic_category'
        db.delete_column('layers_layer', 'topic_category')

        # Deleting field 'Layer.purpose'
        db.delete_column('layers_layer', 'purpose')

        # Deleting field 'Layer.srid'
        db.delete_column('layers_layer', 'srid')

        # Deleting field 'Layer.language'
        db.delete_column('layers_layer', 'language')

        # Deleting field 'Layer.keywords_region'
        db.delete_column('layers_layer', 'keywords_region')

        # Deleting field 'Layer.maintenance_frequency'
        db.delete_column('layers_layer', 'maintenance_frequency')

        # Deleting field 'Layer.csw_anytext'
        db.delete_column('layers_layer', 'csw_anytext')

        # Deleting field 'Layer.csw_type'
        db.delete_column('layers_layer', 'csw_type')

        # Deleting field 'Layer.metadata_uploaded'
        db.delete_column('layers_layer', 'metadata_uploaded')

        # Deleting field 'Layer.csw_wkt_geometry'
        db.delete_column('layers_layer', 'csw_wkt_geometry')

        # Deleting field 'Layer.constraints_use'
        db.delete_column('layers_layer', 'constraints_use')

        # Adding field 'Layer.resourcebase_ptr'
        db.add_column('layers_layer', 'resourcebase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(default=0, to=orm['base.ResourceBase'], unique=True, primary_key=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'Link'
        db.create_table('layers_link', (
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.Layer'])),
            ('mime', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('extension', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('url', self.gf('django.db.models.fields.TextField')(max_length=1000, unique=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('link_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('layers', ['Link'])

        # Adding model 'TopicCategory'
        db.create_table('layers_topiccategory', (
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('layers', ['TopicCategory'])

        # Adding model 'ContactRole'
        db.create_table('layers_contactrole', (
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.Layer'], null=True)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['people.Role'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['people.Profile'])),
        ))
        db.send_create_signal('layers', ['ContactRole'])

        # Adding unique constraint on 'ContactRole', fields ['contact', 'layer', 'role']
        db.create_unique('layers_contactrole', ['contact_id', 'layer_id', 'role_id'])

        # Adding field 'Layer.csw_mdsource'
        db.add_column('layers_layer', 'csw_mdsource', self.gf('django.db.models.fields.CharField')(default='local', max_length=256), keep_default=False)

        # Adding field 'Layer.csw_schema'
        db.add_column('layers_layer', 'csw_schema', self.gf('django.db.models.fields.CharField')(default='http://www.isotc211.org/2005/gmd', max_length=64), keep_default=False)

        # Adding field 'Layer.csw_typename'
        db.add_column('layers_layer', 'csw_typename', self.gf('django.db.models.fields.CharField')(default='gmd:MD_Metadata', max_length=32), keep_default=False)

        # Adding field 'Layer.constraints_other'
        db.add_column('layers_layer', 'constraints_other', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.date'
        db.add_column('layers_layer', 'date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now), keep_default=False)

        # Adding field 'Layer.owner'
        db.add_column('layers_layer', 'owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True), keep_default=False)

        # Adding field 'Layer.uuid'
        db.add_column('layers_layer', 'uuid', self.gf('django.db.models.fields.CharField')(default=0, max_length=36), keep_default=False)

        # Adding field 'Layer.title'
        db.add_column('layers_layer', 'title', self.gf('django.db.models.fields.CharField')(default='', max_length=255), keep_default=False)

        # Adding field 'Layer.date_type'
        db.add_column('layers_layer', 'date_type', self.gf('django.db.models.fields.CharField')(default='publication', max_length=255), keep_default=False)

        # Adding field 'Layer.csw_insert_date'
        db.add_column('layers_layer', 'csw_insert_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True), keep_default=False)

        # Adding field 'Layer.temporal_extent_end'
        db.add_column('layers_layer', 'temporal_extent_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.distribution_url'
        db.add_column('layers_layer', 'distribution_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.metadata_xml'
        db.add_column('layers_layer', 'metadata_xml', self.gf('django.db.models.fields.TextField')(default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>', null=True, blank=True), keep_default=False)

        # Adding field 'Layer.data_quality_statement'
        db.add_column('layers_layer', 'data_quality_statement', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.temporal_extent_start'
        db.add_column('layers_layer', 'temporal_extent_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.bbox_x1'
        db.add_column('layers_layer', 'bbox_x1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.bbox_x0'
        db.add_column('layers_layer', 'bbox_x0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.distribution_description'
        db.add_column('layers_layer', 'distribution_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.abstract'
        db.add_column('layers_layer', 'abstract', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Layer.supplemental_information'
        db.add_column('layers_layer', 'supplemental_information', self.gf('django.db.models.fields.TextField')(default=u'No information provided'), keep_default=False)

        # Adding field 'Layer.edition'
        db.add_column('layers_layer', 'edition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Layer.id'
        db.add_column('layers_layer', 'id', self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True), keep_default=False)

        # Adding field 'Layer.category'
        db.add_column('layers_layer', 'category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.TopicCategory'], null=True, blank=True), keep_default=False)

        # Adding field 'Layer.spatial_representation_type'
        db.add_column('layers_layer', 'spatial_representation_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Layer.bbox_y0'
        db.add_column('layers_layer', 'bbox_y0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.bbox_y1'
        db.add_column('layers_layer', 'bbox_y1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.topic_category'
        db.add_column('layers_layer', 'topic_category', self.gf('django.db.models.fields.CharField')(default='location', max_length=255), keep_default=False)

        # Adding field 'Layer.purpose'
        db.add_column('layers_layer', 'purpose', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.srid'
        db.add_column('layers_layer', 'srid', self.gf('django.db.models.fields.CharField')(default='EPSG:4326', max_length=255), keep_default=False)

        # Adding field 'Layer.language'
        db.add_column('layers_layer', 'language', self.gf('django.db.models.fields.CharField')(default='eng', max_length=3), keep_default=False)

        # Adding field 'Layer.keywords_region'
        db.add_column('layers_layer', 'keywords_region', self.gf('django.db.models.fields.CharField')(default='USA', max_length=3), keep_default=False)

        # Adding field 'Layer.maintenance_frequency'
        db.add_column('layers_layer', 'maintenance_frequency', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Layer.csw_anytext'
        db.add_column('layers_layer', 'csw_anytext', self.gf('django.db.models.fields.TextField')(null=True), keep_default=False)

        # Adding field 'Layer.csw_type'
        db.add_column('layers_layer', 'csw_type', self.gf('django.db.models.fields.CharField')(default='dataset', max_length=32), keep_default=False)

        # Adding field 'Layer.metadata_uploaded'
        db.add_column('layers_layer', 'metadata_uploaded', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Layer.csw_wkt_geometry'
        db.add_column('layers_layer', 'csw_wkt_geometry', self.gf('django.db.models.fields.TextField')(default='SRID=4326;POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))'), keep_default=False)

        # Adding field 'Layer.constraints_use'
        db.add_column('layers_layer', 'constraints_use', self.gf('django.db.models.fields.CharField')(default='copyright', max_length=255), keep_default=False)

        # Deleting field 'Layer.resourcebase_ptr'
        db.delete_column('layers_layer', 'resourcebase_ptr_id')


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
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 15, 4, 29, 40, 959238)'}),
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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 15, 4, 29, 40, 964863)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 15, 4, 29, 40, 964803)'}),
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
        'layers.attribute': {
            'Meta': {'object_name': 'Attribute'},
            'attribute': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'attribute_label': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'attribute_type': ('django.db.models.fields.CharField', [], {'default': "'xsd:string'", 'max_length': '50'}),
            'average': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'display_order': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_stats_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attribute_set'", 'to': "orm['layers.Layer']"}),
            'max': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'median': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'min': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'stddev': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'sum': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'unique_values': ('django.db.models.fields.TextField', [], {'default': "'NA'", 'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'layers.layer': {
            'Meta': {'object_name': 'Layer', '_ormbases': ['base.ResourceBase']},
            'default_style': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'layer_default_style'", 'null': 'True', 'to': "orm['layers.Style']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'popular_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resourcebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.ResourceBase']", 'unique': 'True', 'primary_key': 'True'}),
            'share_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'store': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'storeType': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'styles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'layer_styles'", 'symmetrical': 'False', 'to': "orm['layers.Style']"}),
            'typename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'layers.style': {
            'Meta': {'object_name': 'Style'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'sld_body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sld_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sld_url': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True'}),
            'sld_version': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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

    complete_apps = ['layers']
