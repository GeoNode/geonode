# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'GazetteerEntry'
        db.create_table('gazetteer_gazetteerentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('layer_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('layer_attribute', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('feature_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('feature_fid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('latitude', self.gf('django.db.models.fields.FloatField')()),
            ('longitude', self.gf('django.db.models.fields.FloatField')()),
            ('place_name', self.gf('django.db.models.fields.TextField')()),
            ('start_date', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('julian_start', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('julian_end', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('feature', self.gf('django.contrib.gis.db.models.fields.GeometryField')(null=True, blank=True)),
        ))
        db.send_create_signal('gazetteer', ['GazetteerEntry'])

        # Adding unique constraint on 'GazetteerEntry', fields ['layer_name', 'layer_attribute', 'feature_fid']
        db.create_unique('gazetteer_gazetteerentry', ['layer_name', 'layer_attribute', 'feature_fid'])


    def backwards(self, orm):

        # Removing unique constraint on 'GazetteerEntry', fields ['layer_name', 'layer_attribute', 'feature_fid']
        db.delete_unique('gazetteer_gazetteerentry', ['layer_name', 'layer_attribute', 'feature_fid'])

        # Deleting model 'GazetteerEntry'
        db.delete_table('gazetteer_gazetteerentry')


    models = {
        'gazetteer.gazetteerentry': {
            'Meta': {'unique_together': "(('layer_name', 'layer_attribute', 'feature_fid'),)", 'object_name': 'GazetteerEntry'},
            'end_date': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'feature': ('django.contrib.gis.db.models.fields.GeometryField', [], {'null': 'True', 'blank': 'True'}),
            'feature_fid': ('django.db.models.fields.BigIntegerField', [], {}),
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'julian_end': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'julian_start': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'layer_attribute': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'layer_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'longitude': ('django.db.models.fields.FloatField', [], {}),
            'place_name': ('django.db.models.fields.TextField', [], {}),
            'project': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['gazetteer']
