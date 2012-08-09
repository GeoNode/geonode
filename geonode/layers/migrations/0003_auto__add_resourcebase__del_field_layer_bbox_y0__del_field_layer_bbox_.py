# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ResourceBase'
        db.create_table('layers_resourcebase', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('date_type', self.gf('django.db.models.fields.CharField')(default='publication', max_length=255)),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('abstract', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('purpose', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('maintenance_frequency', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('keywords_region', self.gf('django.db.models.fields.CharField')(default='USA', max_length=3)),
            ('constraints_use', self.gf('django.db.models.fields.CharField')(default='copyright', max_length=255)),
            ('constraints_other', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('spatial_representation_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='eng', max_length=3)),
            ('topic_category', self.gf('django.db.models.fields.CharField')(default='location', max_length=255)),
            ('temporal_extent_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('temporal_extent_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('supplemental_information', self.gf('django.db.models.fields.TextField')(default=u'No information provided')),
            ('distribution_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('distribution_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('data_quality_statement', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bbox_x0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('bbox_x1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('bbox_y0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('bbox_y1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('srid', self.gf('django.db.models.fields.CharField')(default='EPSG:4326', max_length=255)),
        ))
        db.send_create_signal('layers', ['ResourceBase'])

        # Deleting field 'Layer.bbox_y0'
        db.delete_column('layers_layer', 'bbox_y0')

        # Deleting field 'Layer.bbox_y1'
        db.delete_column('layers_layer', 'bbox_y1')

        # Deleting field 'Layer.bbox_x1'
        db.delete_column('layers_layer', 'bbox_x1')

        # Deleting field 'Layer.bbox_x0'
        db.delete_column('layers_layer', 'bbox_x0')

        # Deleting field 'Layer.topic_category'
        db.delete_column('layers_layer', 'topic_category')

        # Deleting field 'Layer.distribution_description'
        db.delete_column('layers_layer', 'distribution_description')

        # Deleting field 'Layer.temporal_extent_end'
        db.delete_column('layers_layer', 'temporal_extent_end')

        # Deleting field 'Layer.abstract'
        db.delete_column('layers_layer', 'abstract')

        # Deleting field 'Layer.srid'
        db.delete_column('layers_layer', 'srid')

        # Deleting field 'Layer.constraints_other'
        db.delete_column('layers_layer', 'constraints_other')

        # Deleting field 'Layer.edition'
        db.delete_column('layers_layer', 'edition')

        # Deleting field 'Layer.purpose'
        db.delete_column('layers_layer', 'purpose')

        # Deleting field 'Layer.date'
        db.delete_column('layers_layer', 'date')

        # Deleting field 'Layer.id'
        db.delete_column('layers_layer', 'id')

        # Deleting field 'Layer.distribution_url'
        db.delete_column('layers_layer', 'distribution_url')

        # Deleting field 'Layer.uuid'
        db.delete_column('layers_layer', 'uuid')

        # Deleting field 'Layer.spatial_representation_type'
        db.delete_column('layers_layer', 'spatial_representation_type')

        # Deleting field 'Layer.language'
        db.delete_column('layers_layer', 'language')

        # Deleting field 'Layer.data_quality_statement'
        db.delete_column('layers_layer', 'data_quality_statement')

        # Deleting field 'Layer.keywords_region'
        db.delete_column('layers_layer', 'keywords_region')

        # Deleting field 'Layer.maintenance_frequency'
        db.delete_column('layers_layer', 'maintenance_frequency')

        # Deleting field 'Layer.supplemental_information'
        db.delete_column('layers_layer', 'supplemental_information')

        # Deleting field 'Layer.owner'
        db.delete_column('layers_layer', 'owner_id')

        # Deleting field 'Layer.temporal_extent_start'
        db.delete_column('layers_layer', 'temporal_extent_start')

        # Deleting field 'Layer.title'
        db.delete_column('layers_layer', 'title')

        # Deleting field 'Layer.date_type'
        db.delete_column('layers_layer', 'date_type')

        # Deleting field 'Layer.constraints_use'
        db.delete_column('layers_layer', 'constraints_use')

        # Adding field 'Layer.resourcebase_ptr'
        db.add_column('layers_layer', 'resourcebase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(default=-1, to=orm['layers.ResourceBase'], unique=True, primary_key=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'ResourceBase'
        db.delete_table('layers_resourcebase')

        # Adding field 'Layer.bbox_y0'
        db.add_column('layers_layer', 'bbox_y0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.bbox_y1'
        db.add_column('layers_layer', 'bbox_y1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.bbox_x1'
        db.add_column('layers_layer', 'bbox_x1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.bbox_x0'
        db.add_column('layers_layer', 'bbox_x0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True), keep_default=False)

        # Adding field 'Layer.topic_category'
        db.add_column('layers_layer', 'topic_category', self.gf('django.db.models.fields.CharField')(default='location', max_length=255), keep_default=False)

        # Adding field 'Layer.distribution_description'
        db.add_column('layers_layer', 'distribution_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.temporal_extent_end'
        db.add_column('layers_layer', 'temporal_extent_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.abstract'
        db.add_column('layers_layer', 'abstract', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Layer.srid'
        db.add_column('layers_layer', 'srid', self.gf('django.db.models.fields.CharField')(default='EPSG:4326', max_length=255), keep_default=False)

        # Adding field 'Layer.constraints_other'
        db.add_column('layers_layer', 'constraints_other', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.edition'
        db.add_column('layers_layer', 'edition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Layer.purpose'
        db.add_column('layers_layer', 'purpose', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.date'
        db.add_column('layers_layer', 'date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now), keep_default=False)

        # User chose to not deal with backwards NULL issues for 'Layer.id'
        raise RuntimeError("Cannot reverse this migration. 'Layer.id' and its values cannot be restored.")

        # Adding field 'Layer.distribution_url'
        db.add_column('layers_layer', 'distribution_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # User chose to not deal with backwards NULL issues for 'Layer.uuid'
        raise RuntimeError("Cannot reverse this migration. 'Layer.uuid' and its values cannot be restored.")

        # Adding field 'Layer.spatial_representation_type'
        db.add_column('layers_layer', 'spatial_representation_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Layer.language'
        db.add_column('layers_layer', 'language', self.gf('django.db.models.fields.CharField')(default='eng', max_length=3), keep_default=False)

        # Adding field 'Layer.data_quality_statement'
        db.add_column('layers_layer', 'data_quality_statement', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Layer.keywords_region'
        db.add_column('layers_layer', 'keywords_region', self.gf('django.db.models.fields.CharField')(default='USA', max_length=3), keep_default=False)

        # Adding field 'Layer.maintenance_frequency'
        db.add_column('layers_layer', 'maintenance_frequency', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Layer.supplemental_information'
        db.add_column('layers_layer', 'supplemental_information', self.gf('django.db.models.fields.TextField')(default=u'No information provided'), keep_default=False)

        # Adding field 'Layer.owner'
        db.add_column('layers_layer', 'owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True), keep_default=False)

        # Adding field 'Layer.temporal_extent_start'
        db.add_column('layers_layer', 'temporal_extent_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # User chose to not deal with backwards NULL issues for 'Layer.title'
        raise RuntimeError("Cannot reverse this migration. 'Layer.title' and its values cannot be restored.")

        # Adding field 'Layer.date_type'
        db.add_column('layers_layer', 'date_type', self.gf('django.db.models.fields.CharField')(default='publication', max_length=255), keep_default=False)

        # Adding field 'Layer.constraints_use'
        db.add_column('layers_layer', 'constraints_use', self.gf('django.db.models.fields.CharField')(default='copyright', max_length=255), keep_default=False)

        # Deleting field 'Layer.resourcebase_ptr'
        db.delete_column('layers_layer', 'resourcebase_ptr_id')


    models = {
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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 8, 8, 18, 43, 53, 807539)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 8, 8, 18, 43, 53, 807425)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'layers.contactrole': {
            'Meta': {'unique_together': "(('contact', 'layer', 'role'),)", 'object_name': 'ContactRole'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Contact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['layers.Layer']", 'null': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Role']"})
        },
        'layers.layer': {
            'Meta': {'object_name': 'Layer', '_ormbases': ['layers.ResourceBase']},
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['people.Contact']", 'through': "orm['layers.ContactRole']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'resourcebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['layers.ResourceBase']", 'unique': 'True', 'primary_key': 'True'}),
            'store': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'storeType': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'typename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'layers.link': {
            'Meta': {'object_name': 'Link'},
            'extension': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['layers.Layer']"}),
            'link_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mime': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        'layers.resourcebase': {
            'Meta': {'object_name': 'ResourceBase'},
            'abstract': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bbox_x0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_x1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'constraints_other': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'constraints_use': ('django.db.models.fields.CharField', [], {'default': "'copyright'", 'max_length': '255'}),
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
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'purpose': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'spatial_representation_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'srid': ('django.db.models.fields.CharField', [], {'default': "'EPSG:4326'", 'max_length': '255'}),
            'supplemental_information': ('django.db.models.fields.TextField', [], {'default': "u'No information provided'"}),
            'temporal_extent_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'temporal_extent_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'topic_category': ('django.db.models.fields.CharField', [], {'default': "'location'", 'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        'people.contact': {
            'Meta': {'object_name': 'Contact'},
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'voice': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'people.role': {
            'Meta': {'object_name': 'Role'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
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
