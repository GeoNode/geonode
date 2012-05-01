# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Contact'
        db.create_table('maps_contact', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('organization', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('position', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('voice', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('fax', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('delivery', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('area', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('zipcode', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('display_email', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_org_member', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('member_expiration_dt', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2012, 2, 23, 10, 22, 44, 871274))),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('maps', ['Contact'])

        # Adding model 'LayerCategory'
        db.create_table('maps_layercategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('maps', ['LayerCategory'])

        # Adding model 'Layer'
        db.create_table('maps_layer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('workspace', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('store', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('storeType', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('typename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('date_type', self.gf('django.db.models.fields.CharField')(default='publication', max_length=255)),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('abstract', self.gf('django.db.models.fields.TextField')()),
            ('purpose', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('maintenance_frequency', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('keywords', self.gf('django.db.models.fields.TextField')(null=True)),
            ('keywords_region', self.gf('django.db.models.fields.CharField')(default='GLO', max_length=3)),
            ('constraints_use', self.gf('django.db.models.fields.CharField')(default='copyright', max_length=255)),
            ('constraints_other', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('spatial_representation_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='eng', max_length=3)),
            ('topic_category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.LayerCategory'], null=True, blank=True)),
            ('temporal_extent_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('temporal_extent_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('geographic_bounding_box', self.gf('django.db.models.fields.TextField')()),
            ('supplemental_information', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('distribution_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('distribution_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('srs', self.gf('django.db.models.fields.CharField')(default='EPSG:4326', max_length=24, null=True, blank=True)),
            ('bbox', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('llbbox', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('data_quality_statement', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('maps', ['Layer'])

        # Adding model 'LayerAttribute'
        db.create_table('maps_layerattribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attribute_set', to=orm['maps.Layer'])),
            ('attribute', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('attribute_label', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('attribute_type', self.gf('django.db.models.fields.CharField')(default='xsd:string', max_length=50)),
            ('searchable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('display_order', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('maps', ['LayerAttribute'])

        # Adding model 'Map'
        db.create_table('maps_map', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('abstract', self.gf('django.db.models.fields.TextField')()),
            ('zoom', self.gf('django.db.models.fields.IntegerField')()),
            ('projection', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('center_x', self.gf('django.db.models.fields.FloatField')()),
            ('center_y', self.gf('django.db.models.fields.FloatField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('urlsuffix', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('officialurl', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(default=u'<h3>The Harvard WorldMap Project</h3><p>WorldMap is an open source web mapping system that is currentlyunder construction. It is built to assist academic research andteaching as well as the general public and supports discovery,investigation, analysis, visualization, communication and archivingof multi-disciplinary, multi-source and multi-format data,organized spatially and temporally.</p><p>The first instance of WorldMap, focused on the continent ofAfrica, is called AfricaMap. Since its beta release in November of2008, the framework has been implemented in several geographiclocations with different research foci, including metro Boston,East Asia, Vermont, Harvard Forest and the city of Paris. These webmapping applications are used in courses as well as by individualresearchers.</p><h3>Introduction to the WorldMap Project</h3><p>WorldMap solves the problem of discovering where things happen.It draws together an array of public maps and scholarly data tocreate a common source where users can:</p><ol><li>Interact with the best available public data for acity/region/continent</li><li>See the whole of that area yet also zoom in to particularplaces</li><li>Accumulate both contemporary and historical data supplied byresearchers and make it permanently accessible online</li><li>Work collaboratively across disciplines and organizations withspatial information in an online environment</li></ol><p>The WorldMap project aims to accomplish these goals in stages,with public and private support. It draws on the basic insight ofgeographic information systems that spatiotemporal data becomesmore meaningful as more "layers" are added, and makes use of tilingand indexing approaches to facilitate rapid search andvisualization of large volumes of disparate data.</p><p>WorldMap aims to augment existing initiatives for globallysharing spatial data and technology such as <a target="_blank" href="http://www.gsdi.org/">GSDI</a> (Global Spatial DataInfrastructure).WorldMap makes use of <a target="_blank" href="http://www.opengeospatial.org/">OGC</a> (Open GeospatialConsortium) compliant web services such as <a target="_blank" href="http://en.wikipedia.org/wiki/Web_Map_Service">WMS</a> (WebMap Service), emerging open standards such as <a target="_blank" href="http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification">WMS-C</a>(cached WMS), and standards-based metadata formats, to enableWorldMap data layers to be inserted into existing datainfrastructures.&nbsp;<br><br>All WorldMap source code will be made available as <a target="_blank" href="http://www.opensource.org/">Open Source</a> for others to useand improve upon.</p>', null=True, blank=True)),
            ('use_custom_template', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('group_params', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('maps', ['Map'])

        # Adding model 'MapSnapshot'
        db.create_table('maps_mapsnapshot', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('map', self.gf('django.db.models.fields.related.ForeignKey')(related_name='snapshot_set', to=orm['maps.Map'])),
            ('config', self.gf('django.db.models.fields.TextField')()),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('maps', ['MapSnapshot'])

        # Adding model 'SocialExplorerLocation'
        db.create_table('maps_socialexplorerlocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('map', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jump_set', to=orm['maps.Map'])),
            ('url', self.gf('django.db.models.fields.URLField')(default='http://www.socialexplorer.com/pub/maps/map3.aspx?g=0&mapi=SE0012&themei=B23A1CEE3D8D405BA2B079DDF5DE9402', max_length=200)),
            ('title', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('maps', ['SocialExplorerLocation'])

        # Adding model 'MapLayer'
        db.create_table('maps_maplayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('map', self.gf('django.db.models.fields.related.ForeignKey')(related_name='layer_set', to=orm['maps.Map'])),
            ('stack_order', self.gf('django.db.models.fields.IntegerField')()),
            ('format', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('opacity', self.gf('django.db.models.fields.FloatField')(default=1.0)),
            ('styles', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('transparent', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('fixed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('group', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('visibility', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('ows_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('layer_params', self.gf('django.db.models.fields.TextField')()),
            ('source_params', self.gf('django.db.models.fields.TextField')()),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('maps', ['MapLayer'])

        # Adding model 'Role'
        db.create_table('maps_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('created_dttm', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('maps', ['Role'])

        # Adding M2M table for field permissions on 'Role'
        db.create_table('maps_role_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('role', models.ForeignKey(orm['maps.role'], null=False)),
            ('permission', models.ForeignKey(orm['auth.permission'], null=False))
        ))
        db.create_unique('maps_role_permissions', ['role_id', 'permission_id'])

        # Adding model 'ContactRole'
        db.create_table('maps_contactrole', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.Contact'])),
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.Layer'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.Role'])),
        ))
        db.send_create_signal('maps', ['ContactRole'])

        # Adding unique constraint on 'ContactRole', fields ['contact', 'layer', 'role']
        db.create_unique('maps_contactrole', ['contact_id', 'layer_id', 'role_id'])

        # Adding model 'MapStats'
        db.create_table('maps_mapstats', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('map', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.Map'], unique=True)),
            ('visits', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('uniques', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('maps', ['MapStats'])

        # Adding model 'LayerStats'
        db.create_table('maps_layerstats', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['maps.Layer'], unique=True)),
            ('visits', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('uniques', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('downloads', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('maps', ['LayerStats'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ContactRole', fields ['contact', 'layer', 'role']
        db.delete_unique('maps_contactrole', ['contact_id', 'layer_id', 'role_id'])

        # Deleting model 'Contact'
        db.delete_table('maps_contact')

        # Deleting model 'LayerCategory'
        db.delete_table('maps_layercategory')

        # Deleting model 'Layer'
        db.delete_table('maps_layer')

        # Deleting model 'LayerAttribute'
        db.delete_table('maps_layerattribute')

        # Deleting model 'Map'
        db.delete_table('maps_map')

        # Deleting model 'MapSnapshot'
        db.delete_table('maps_mapsnapshot')

        # Deleting model 'SocialExplorerLocation'
        db.delete_table('maps_socialexplorerlocation')

        # Deleting model 'MapLayer'
        db.delete_table('maps_maplayer')

        # Deleting model 'Role'
        db.delete_table('maps_role')

        # Removing M2M table for field permissions on 'Role'
        db.delete_table('maps_role_permissions')

        # Deleting model 'ContactRole'
        db.delete_table('maps_contactrole')

        # Deleting model 'MapStats'
        db.delete_table('maps_mapstats')

        # Deleting model 'LayerStats'
        db.delete_table('maps_layerstats')


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
        'maps.contact': {
            'Meta': {'object_name': 'Contact'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delivery': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'display_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_org_member': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'member_expiration_dt': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2012, 2, 23, 10, 22, 44, 871274)'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'voice': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'maps.contactrole': {
            'Meta': {'unique_together': "(('contact', 'layer', 'role'),)", 'object_name': 'ContactRole'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maps.Contact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maps.Layer']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maps.Role']"})
        },
        'maps.layer': {
            'Meta': {'object_name': 'Layer'},
            'abstract': ('django.db.models.fields.TextField', [], {}),
            'bbox': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'constraints_other': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'constraints_use': ('django.db.models.fields.CharField', [], {'default': "'copyright'", 'max_length': '255'}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['maps.Contact']", 'through': "orm['maps.ContactRole']", 'symmetrical': 'False'}),
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_quality_statement': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_type': ('django.db.models.fields.CharField', [], {'default': "'publication'", 'max_length': '255'}),
            'distribution_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'geographic_bounding_box': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'keywords_region': ('django.db.models.fields.CharField', [], {'default': "'GLO'", 'max_length': '3'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'eng'", 'max_length': '3'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'llbbox': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'maintenance_frequency': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'purpose': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'spatial_representation_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'srs': ('django.db.models.fields.CharField', [], {'default': "'EPSG:4326'", 'max_length': '24', 'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'storeType': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'supplemental_information': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'temporal_extent_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'temporal_extent_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'topic_category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maps.LayerCategory']", 'null': 'True', 'blank': 'True'}),
            'typename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'downloadable': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'maps.layerattribute': {
            'Meta': {'object_name': 'LayerAttribute'},
            'attribute': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'attribute_label': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'attribute_type': ('django.db.models.fields.CharField', [], {'default': "'xsd:string'", 'max_length': '50'}),
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_order': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attribute_set'", 'to': "orm['maps.Layer']"}),
            'searchable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'maps.layercategory': {
            'Meta': {'object_name': 'LayerCategory'},
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'maps.layerstats': {
            'Meta': {'object_name': 'LayerStats'},
            'downloads': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maps.Layer']", 'unique': 'True'}),
            'uniques': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'visits': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'maps.map': {
            'Meta': {'object_name': 'Map'},
            'abstract': ('django.db.models.fields.TextField', [], {}),
            'center_x': ('django.db.models.fields.FloatField', [], {}),
            'center_y': ('django.db.models.fields.FloatField', [], {}),
            'content': ('django.db.models.fields.TextField', [], {'default': 'u\'<h3>The Harvard WorldMap Project</h3><p>WorldMap is an open source web mapping system that is currentlyunder construction. It is built to assist academic research andteaching as well as the general public and supports discovery,investigation, analysis, visualization, communication and archivingof multi-disciplinary, multi-source and multi-format data,organized spatially and temporally.</p><p>The first instance of WorldMap, focused on the continent ofAfrica, is called AfricaMap. Since its beta release in November of2008, the framework has been implemented in several geographiclocations with different research foci, including metro Boston,East Asia, Vermont, Harvard Forest and the city of Paris. These webmapping applications are used in courses as well as by individualresearchers.</p><h3>Introduction to the WorldMap Project</h3><p>WorldMap solves the problem of discovering where things happen.It draws together an array of public maps and scholarly data tocreate a common source where users can:</p><ol><li>Interact with the best available public data for acity/region/continent</li><li>See the whole of that area yet also zoom in to particularplaces</li><li>Accumulate both contemporary and historical data supplied byresearchers and make it permanently accessible online</li><li>Work collaboratively across disciplines and organizations withspatial information in an online environment</li></ol><p>The WorldMap project aims to accomplish these goals in stages,with public and private support. It draws on the basic insight ofgeographic information systems that spatiotemporal data becomesmore meaningful as more "layers" are added, and makes use of tilingand indexing approaches to facilitate rapid search andvisualization of large volumes of disparate data.</p><p>WorldMap aims to augment existing initiatives for globallysharing spatial data and technology such as <a target="_blank" href="http://www.gsdi.org/">GSDI</a> (Global Spatial DataInfrastructure).WorldMap makes use of <a target="_blank" href="http://www.opengeospatial.org/">OGC</a> (Open GeospatialConsortium) compliant web services such as <a target="_blank" href="http://en.wikipedia.org/wiki/Web_Map_Service">WMS</a> (WebMap Service), emerging open standards such as <a target="_blank" href="http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification">WMS-C</a>(cached WMS), and standards-based metadata formats, to enableWorldMap data layers to be inserted into existing datainfrastructures.&nbsp;<br><br>All WorldMap source code will be made available as <a target="_blank" href="http://www.opensource.org/">Open Source</a> for others to useand improve upon.</p>\'', 'null': 'True', 'blank': 'True'}),
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group_params': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'officialurl': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'projection': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'urlsuffix': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'use_custom_template': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'zoom': ('django.db.models.fields.IntegerField', [], {})
        },
        'maps.maplayer': {
            'Meta': {'ordering': "['stack_order']", 'object_name': 'MapLayer'},
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fixed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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
        'maps.mapsnapshot': {
            'Meta': {'object_name': 'MapSnapshot'},
            'config': ('django.db.models.fields.TextField', [], {}),
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'snapshot_set'", 'to': "orm['maps.Map']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'maps.mapstats': {
            'Meta': {'object_name': 'MapStats'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['maps.Map']", 'unique': 'True'}),
            'uniques': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'visits': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'maps.role': {
            'Meta': {'object_name': 'Role'},
            'created_dttm': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'maps.socialexplorerlocation': {
            'Meta': {'object_name': 'SocialExplorerLocation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jump_set'", 'to': "orm['maps.Map']"}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'default': "'http://www.socialexplorer.com/pub/maps/map3.aspx?g=0&mapi=SE0012&themei=B23A1CEE3D8D405BA2B079DDF5DE9402'", 'max_length': '200'})
        }
    }

    complete_apps = ['maps']
