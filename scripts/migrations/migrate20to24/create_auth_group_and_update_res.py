import os, sys, ConfigParser

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gn_migration.cfg'))
geonode_path = config.get('path', 'geonode_path')
settings_path = config.get('path', 'settings_path')
sys.path.append(geonode_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_path)

from geonode.groups.models import GroupProfile
from geonode.people.models import Profile
from geonode.base.models import ResourceBase

print 'Creating the authenticated group...'
gp = GroupProfile.objects.get_or_create(
    title='Authenticated GeoNode Users',
    slug='authenticated',
    description='Group containg all of the registered GeoNode users',
    access='public',
)[0]
# assign all existing users to this group
print 'Now adding all users to the group...'
for profile in Profile.objects.all():
    if profile.username != 'AnonymousUser':
        print 'Adding %s to the group' % profile.username
        if gp.user_is_member(profile):
            print 'this user is already member of the group!'
        else:
            gp.join(profile)

# updates resources
print 'Updating resources...'

for res in ResourceBase.objects.all():
    try:
        if res.polymorphic_ctype.name == 'layer':
            print 'Updating layer %s' % res.title
            layer = res.layer
            layer.save()
        if res.polymorphic_ctype.name == 'map':
            print 'Updating map %s' % res.title
            m = res.map
            m.save()
        if res.polymorphic_ctype.name == 'document':
            print 'Updating document %s' % res.title
            d = res.document
            d.save()
    except Exception as error:
        print type(error)
        pass
