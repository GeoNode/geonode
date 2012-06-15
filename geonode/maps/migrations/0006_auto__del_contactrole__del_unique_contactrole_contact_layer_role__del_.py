# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'ContactRole', fields ['contact', 'layer', 'role']
        db.delete_unique('maps_contactrole', ['contact_id', 'layer_id', 'role_id'])

        # Deleting model 'ContactRole'
        db.delete_table('maps_contactrole')

        # Deleting model 'Role'
        db.delete_table('maps_role')

        # Removing M2M table for field permissions on 'Role'
        db.delete_table('maps_role_permissions')

        # Deleting model 'Layer'
        db.delete_table('maps_layer')

        # Adding field 'Map.bbox_top'
        db.add_column('maps_map', 'bbox_top', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.bbox_bottom'
        db.add_column('maps_map', 'bbox_bottom', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.bbox_right'
        db.add_column('maps_map', 'bbox_right', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'Map.bbox_left'
        db.add_column('maps_map', 'bbox_left', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'ContactRole'
        db.create_table('maps_contactrole', (
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.Layer'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.Role'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['people.Contact'])),
        ))
        db.send_create_signal('maps', ['ContactRole'])

        # Adding unique constraint on 'ContactRole', fields ['contact', 'layer', 'role']
        db.create_unique('maps_contactrole', ['contact_id', 'layer_id', 'role_id'])

        # Adding model 'Role'
        db.create_table('maps_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
        ))
        db.send_create_signal('maps', ['Role'])

        # Adding M2M table for field permissions on 'Role'
        db.create_table('maps_role_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('role', models.ForeignKey(orm['maps.role'], null=False)),
            ('permission', models.ForeignKey(orm['auth.permission'], null=False))
        ))
        db.create_unique('maps_role_permissions', ['role_id', 'permission_id'])

        # Adding model 'Layer'
        db.create_table('maps_layer', (
            ('constraints_other', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('abstract', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('geographic_bounding_box', self.gf('django.db.models.fields.TextField')()),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('distribution_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('spatial_representation_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('storeType', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('date_type', self.gf('django.db.models.fields.CharField')(default='publication', max_length=255)),
            ('store', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('distribution_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('topic_category', self.gf('django.db.models.fields.CharField')(default='location', max_length=255)),
            ('purpose', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('temporal_extent_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('data_quality_statement', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='eng', max_length=3)),
            ('keywords_region', self.gf('django.db.models.fields.CharField')(default='USA', max_length=3)),
            ('maintenance_frequency', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('supplemental_information', self.gf('django.db.models.fields.TextField')(default=u'You can customize the template to suit your needs. You can add and remove fields and fill out default information (e.g. contact details). Fields you can not change in the default view may be accessible in the more comprehensive (and more complex) advanced view. You can even use the XML editor to create custom structures, but they have to be validated by the system, so know what you do :-)')),
            ('typename', self.gf('django.db.models.fields.CharField')(max_length=128, unique=True)),
            ('workspace', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('temporal_extent_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('constraints_use', self.gf('django.db.models.fields.CharField')(default='copyright', max_length=255)),
        ))
        db.send_create_signal('maps', ['Layer'])

        # Deleting field 'Map.bbox_top'
        db.delete_column('maps_map', 'bbox_top')

        # Deleting field 'Map.bbox_bottom'
        db.delete_column('maps_map', 'bbox_bottom')

        # Deleting field 'Map.bbox_right'
        db.delete_column('maps_map', 'bbox_right')

        # Deleting field 'Map.bbox_left'
        db.delete_column('maps_map', 'bbox_left')


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 6, 14, 20, 6, 59, 566796)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 6, 14, 20, 6, 59, 566653)'}),
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
        'maps.map': {
            'Meta': {'object_name': 'Map'},
            'abstract': ('django.db.models.fields.TextField', [], {}),
            'bbox_bottom': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'bbox_left': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'bbox_right': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'bbox_top': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'center_x': ('django.db.models.fields.FloatField', [], {}),
            'center_y': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'projection': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'zoom': ('django.db.models.fields.IntegerField', [], {})
        },
        'maps.maplayer': {
            'Meta': {'ordering': "['stack_order']", 'object_name': 'MapLayer'},
            'fixed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer_params': ('django.db.models.fields.TextField', [], {}),
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
