# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from geonode.settings import GAZETTEER_DB_ALIAS


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'GazetteerEntry.username'
        db.add_column('gazetteer_gazetteerentry', 'username', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True), keep_default=False)

    def backwards(self, orm):
        # Deleting field 'GazetteerEntry.username'
        db.delete_column('gazetteer_gazetteerentry', 'username')

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
            'start_date': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['gazetteer']
