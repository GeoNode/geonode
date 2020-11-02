# flake8: noqa
# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EntryCategory'
        db.create_table(u'frequently_entrycategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('fixed_position', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('last_rank', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'frequently', ['EntryCategory'])

        # Adding model 'Entry'
        db.create_table(u'frequently_entry', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('question', self.gf('django.db.models.fields.TextField')(max_length=2000)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('answer', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 23, 0, 0))),
            ('last_view_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 23, 0, 0))),
            ('amount_of_views', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('fixed_position', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('upvotes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('downvotes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('submitted_by', self.gf('django.db.models.fields.EmailField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'frequently', ['Entry'])

        # Adding M2M table for field category on 'Entry'
        m2m_table_name = db.shorten_name(u'frequently_entry_category')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entry', models.ForeignKey(orm[u'frequently.entry'], null=False)),
            ('entrycategory', models.ForeignKey(orm[u'frequently.entrycategory'], null=False))
        ))
        db.create_unique(m2m_table_name, ['entry_id', 'entrycategory_id'])

        # Adding model 'Feedback'
        db.create_table(u'frequently_feedback', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['frequently.Entry'], null=True, blank=True)),
            ('remark', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('submission_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 23, 0, 0))),
            ('validation', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal(u'frequently', ['Feedback'])


    def backwards(self, orm):
        # Deleting model 'EntryCategory'
        db.delete_table(u'frequently_entrycategory')

        # Deleting model 'Entry'
        db.delete_table(u'frequently_entry')

        # Removing M2M table for field category on 'Entry'
        db.delete_table(db.shorten_name(u'frequently_entry_category'))

        # Deleting model 'Feedback'
        db.delete_table(u'frequently_feedback')


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
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
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
        u'frequently.entry': {
            'Meta': {'ordering': "['fixed_position', 'question']", 'object_name': 'Entry'},
            'amount_of_views': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'answer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'entries'", 'symmetrical': 'False', 'to': u"orm['frequently.EntryCategory']"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 23, 0, 0)'}),
            'downvotes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'fixed_position': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_view_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 23, 0, 0)'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'question': ('django.db.models.fields.TextField', [], {'max_length': '2000'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'submitted_by': ('django.db.models.fields.EmailField', [], {'max_length': '100', 'blank': 'True'}),
            'upvotes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'frequently.entrycategory': {
            'Meta': {'ordering': "['fixed_position', 'name']", 'object_name': 'EntryCategory'},
            'fixed_position': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_rank': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'frequently.feedback': {
            'Meta': {'object_name': 'Feedback'},
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['frequently.Entry']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remark': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'submission_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 23, 0, 0)'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'validation': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['frequently']