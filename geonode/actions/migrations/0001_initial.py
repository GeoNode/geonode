# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Action'
        db.create_table('actions_action', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_type', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('args', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
        ))
        db.send_create_signal('actions', ['Action'])


    def backwards(self, orm):
        # Deleting model 'Action'
        db.delete_table('actions_action')


    models = {
        'actions.action': {
            'Meta': {'object_name': 'Action'},
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'args': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'})
        }
    }

    complete_apps = ['actions']