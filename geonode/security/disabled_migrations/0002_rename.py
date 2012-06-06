# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        db.rename_table('core_objectrole', 'security_objectrole')
        db.rename_table('core_userobjectrolemapping', 'security_userobjectrolemapping')
        db.rename_table('core_genericobjectrolemapping', 'security_genericrobjectrolemapping')
        db.rename_table('core_objectrole_permissions', 'security_objectrole_permissions')

#FIXME(commenting this out because it causes syncdb to fail)       
#        if not db.dry_run:
#            # For permissions to work properly after migrating
#            ct = orm['contenttypes.contenttype']
#            core_contenttypes = ct.objects.filter(app_label='core')
#            core_contenttypes.update(app_label='security')

    def backwards(self, orm):
        db.rename_table('security_objectrole', 'core_objectrole')
        db.rename_table('security_userobjectrolemapping', 'core_userobjectrolemapping')
        db.rename_table('security_genericobjectrolemapping', 'core_genericrobjectrolemapping')
        db.rename_table('security_objectrole_permissions', 'core_objectrole_permissions')
