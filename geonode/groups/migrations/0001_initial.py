# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Group'
        db.create_table(u'groups_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('logo', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('access', self.gf('django.db.models.fields.CharField')(default="public'", max_length=15)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'groups', ['Group'])

        # Adding model 'GroupMember'
        db.create_table(u'groups_groupmember', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['groups.Group'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'groups', ['GroupMember'])

        # Adding model 'GroupInvitation'
        db.create_table(u'groups_groupinvitation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invitations', to=orm['groups.Group'])),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pg_invitations_received', null=True, to=orm['auth.User'])),
            ('from_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pg_invitations_sent', to=orm['auth.User'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('state', self.gf('django.db.models.fields.CharField')(default='sent', max_length=10)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'groups', ['GroupInvitation'])

        # Adding unique constraint on 'GroupInvitation', fields ['group', 'email']
        db.create_unique(u'groups_groupinvitation', ['group_id', 'email'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'GroupInvitation', fields ['group', 'email']
        db.delete_unique(u'groups_groupinvitation', ['group_id', 'email'])

        # Deleting model 'Group'
        db.delete_table(u'groups_group')

        # Deleting model 'GroupMember'
        db.delete_table(u'groups_groupmember')

        # Deleting model 'GroupInvitation'
        db.delete_table(u'groups_groupinvitation')


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
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 4, 1, 12, 12, 0, 559462)'}),
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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 4, 1, 12, 12, 0, 561425)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 4, 1, 12, 12, 0, 560800)'}),
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
        u'groups.group': {
            'Meta': {'object_name': 'Group'},
            'access': ('django.db.models.fields.CharField', [], {'default': '"public\'"', 'max_length': '15'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'logo': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'groups.groupinvitation': {
            'Meta': {'unique_together': "[('group', 'email')]", 'object_name': 'GroupInvitation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pg_invitations_sent'", 'to': u"orm['auth.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations'", 'to': u"orm['groups.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'sent'", 'max_length': '10'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pg_invitations_received'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        u'groups.groupmember': {
            'Meta': {'object_name': 'GroupMember'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['groups.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['groups']
