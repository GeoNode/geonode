# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'ObjectRole'
        db.create_table('core_objectrole', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('codename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('list_order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('core', ['ObjectRole'])

        # Adding unique constraint on 'ObjectRole', fields ['content_type', 'codename']
        db.create_unique('core_objectrole', ['content_type_id', 'codename'])

        # Adding M2M table for field permissions on 'ObjectRole'
        db.create_table('core_objectrole_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('objectrole', models.ForeignKey(orm['core.objectrole'], null=False)),
            ('permission', models.ForeignKey(orm['auth.permission'], null=False))
        ))
        db.create_unique('core_objectrole_permissions', ['objectrole_id', 'permission_id'])

        # Adding model 'UserObjectRoleMapping'
        db.create_table('core_userobjectrolemapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='role_mappings', to=orm['auth.User'])),
            ('object_ct', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_mappings', to=orm['core.ObjectRole'])),
        ))
        db.send_create_signal('core', ['UserObjectRoleMapping'])

        # Adding unique constraint on 'UserObjectRoleMapping', fields ['user', 'object_ct', 'object_id', 'role']
        db.create_unique('core_userobjectrolemapping', ['user_id', 'object_ct_id', 'object_id', 'role_id'])

        # Adding model 'GenericObjectRoleMapping'
        db.create_table('core_genericobjectrolemapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('object_ct', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(related_name='generic_mappings', to=orm['core.ObjectRole'])),
        ))
        db.send_create_signal('core', ['GenericObjectRoleMapping'])

        # Adding unique constraint on 'GenericObjectRoleMapping', fields ['subject', 'object_ct', 'object_id', 'role']
        db.create_unique('core_genericobjectrolemapping', ['subject', 'object_ct_id', 'object_id', 'role_id'])


    def backwards(self, orm):

        # Removing unique constraint on 'GenericObjectRoleMapping', fields ['subject', 'object_ct', 'object_id', 'role']
        db.delete_unique('core_genericobjectrolemapping', ['subject', 'object_ct_id', 'object_id', 'role_id'])

        # Removing unique constraint on 'UserObjectRoleMapping', fields ['user', 'object_ct', 'object_id', 'role']
        db.delete_unique('core_userobjectrolemapping', ['user_id', 'object_ct_id', 'object_id', 'role_id'])

        # Removing unique constraint on 'ObjectRole', fields ['content_type', 'codename']
        db.delete_unique('core_objectrole', ['content_type_id', 'codename'])

        # Deleting model 'ObjectRole'
        db.delete_table('core_objectrole')

        # Removing M2M table for field permissions on 'ObjectRole'
        db.delete_table('core_objectrole_permissions')

        # Deleting model 'UserObjectRoleMapping'
        db.delete_table('core_userobjectrolemapping')

        # Deleting model 'GenericObjectRoleMapping'
        db.delete_table('core_genericobjectrolemapping')


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
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
        'core.genericobjectrolemapping': {
            'Meta': {'unique_together': "(('subject', 'object_ct', 'object_id', 'role'),)", 'object_name': 'GenericObjectRoleMapping'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'generic_mappings'", 'to': "orm['core.ObjectRole']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.objectrole': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'ObjectRole'},
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_order': ('django.db.models.fields.IntegerField', [], {}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.userobjectrolemapping': {
            'Meta': {'unique_together': "(('user', 'object_ct', 'object_id', 'role'),)", 'object_name': 'UserObjectRoleMapping'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_mappings'", 'to': "orm['core.ObjectRole']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_mappings'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['core']
