# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ObjectRole'
        db.create_table(u'security_objectrole', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('codename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('list_order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'security', ['ObjectRole'])

        # Adding unique constraint on 'ObjectRole', fields ['content_type', 'codename']
        db.create_unique(u'security_objectrole', ['content_type_id', 'codename'])

        # Adding M2M table for field permissions on 'ObjectRole'
        db.create_table(u'security_objectrole_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('objectrole', models.ForeignKey(orm[u'security.objectrole'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(u'security_objectrole_permissions', ['objectrole_id', 'permission_id'])

        # Adding model 'UserObjectRoleMapping'
        db.create_table(u'security_userobjectrolemapping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='role_mappings', to=orm['auth.User'])),
            ('object_ct', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_mappings', to=orm['security.ObjectRole'])),
        ))
        db.send_create_signal(u'security', ['UserObjectRoleMapping'])

        # Adding unique constraint on 'UserObjectRoleMapping', fields ['user', 'object_ct', 'object_id', 'role']
        db.create_unique(u'security_userobjectrolemapping', ['user_id', 'object_ct_id', 'object_id', 'role_id'])

        # Adding model 'GenericObjectRoleMapping'
        db.create_table(u'security_genericobjectrolemapping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('object_ct', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(related_name='generic_mappings', to=orm['security.ObjectRole'])),
        ))
        db.send_create_signal(u'security', ['GenericObjectRoleMapping'])

        # Adding unique constraint on 'GenericObjectRoleMapping', fields ['subject', 'object_ct', 'object_id', 'role']
        db.create_unique(u'security_genericobjectrolemapping', ['subject', 'object_ct_id', 'object_id', 'role_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'GenericObjectRoleMapping', fields ['subject', 'object_ct', 'object_id', 'role']
        db.delete_unique(u'security_genericobjectrolemapping', ['subject', 'object_ct_id', 'object_id', 'role_id'])

        # Removing unique constraint on 'UserObjectRoleMapping', fields ['user', 'object_ct', 'object_id', 'role']
        db.delete_unique(u'security_userobjectrolemapping', ['user_id', 'object_ct_id', 'object_id', 'role_id'])

        # Removing unique constraint on 'ObjectRole', fields ['content_type', 'codename']
        db.delete_unique(u'security_objectrole', ['content_type_id', 'codename'])

        # Deleting model 'ObjectRole'
        db.delete_table(u'security_objectrole')

        # Removing M2M table for field permissions on 'ObjectRole'
        db.delete_table('security_objectrole_permissions')

        # Deleting model 'UserObjectRoleMapping'
        db.delete_table(u'security_userobjectrolemapping')

        # Deleting model 'GenericObjectRoleMapping'
        db.delete_table(u'security_genericobjectrolemapping')


    models = {
        u'actstream.action': {
            'Meta': {'ordering': "('-timestamp',)", 'object_name': 'Action'},
            'action_object_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'action_object'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'action_object_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'actor_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actor'", 'to': u"orm['contenttypes.ContentType']"}),
            'actor_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'data': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'target_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'target'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'target_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 6, 11, 43, 37, 543340)'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
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
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 6, 11, 43, 37, 542633)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 6, 11, 43, 37, 542253)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'security.genericobjectrolemapping': {
            'Meta': {'unique_together': "(('subject', 'object_ct', 'object_id', 'role'),)", 'object_name': 'GenericObjectRoleMapping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_ct': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'generic_mappings'", 'to': u"orm['security.ObjectRole']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'security.objectrole': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'ObjectRole'},
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_order': ('django.db.models.fields.IntegerField', [], {}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'security.userobjectrolemapping': {
            'Meta': {'unique_together': "(('user', 'object_ct', 'object_id', 'role'),)", 'object_name': 'UserObjectRoleMapping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_ct': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_mappings'", 'to': u"orm['security.ObjectRole']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'role_mappings'", 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['security']
