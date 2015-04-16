import sys
import os

sys.path.append('/home/capooti/git/github/geonode/geonode/geonode')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import glob
from random import randint

from django.core.files import File
from django.conf import settings

from taggit.models import Tag

from geonode.base.models import TopicCategory
from geonode.base.models import Region
from geonode.people.models import Profile
from geonode.documents.models import Document

def get_random_user():
    """ Get a random user """
    users_count = Profile.objects.all().count()
    random_index = randint(0, users_count -1)
    return Profile.objects.all()[random_index]

def assign_random_category(resource):
    """ Assign a random category to a resource """
    random_index = randint(0, TopicCategory.objects.all().count() - 1)
    tc = TopicCategory.objects.all()[random_index]
    resource.category = tc
    resource.save()
    
def assign_keywords(resource):
    """ Assigns up to 5 keywords to resource """
    for i in range(0, randint(0, 5)):
        resource.keywords.add('keyword_%s' % randint(0, n_keywords))
    
def assign_regions(resource):
    """ Assign up to 5 regions to resource """
    for i in range(0, randint(0, 5)):
        random_index = randint(0, Region.objects.all().count() - 1)
        region = Region.objects.all()[random_index]
        resource.regions.add(region)
    
# create users
def create_users(n_users):
    """ Create n users in the database """
    for i in range(3, n_users):
        user = Profile()
        user.username = 'user_%s' % i
        user.save()

def create_document(number):
    """ Creates a new document """
    print 'Generating document %s' % number
    file_list = glob.glob('%s*.jpg' % doc_path)
    random_index = randint(0, len(file_list) -1)
    file_uri = file_list[random_index]
    title = 'Document N. %s' % number
    img_filename = '%s_img.jpg' % number
    doc = Document(title=title, owner=get_random_user())
    doc.save()
    with open(file_uri, 'r') as f:
        img_file = File(f) 
        doc.doc_file.save(img_filename, img_file, True)
    resource = doc.get_self_resource()
    # metadata
    resource.poc = get_random_user()
    resource.metadata_author = get_random_user()
    # category
    assign_random_category(resource)
    # keywords
    assign_keywords(doc)
    # regions
    assign_regions(resource)

# in doc_path set a path containing *.jpg files
doc_path = '/home/capooti/Desktop/maps/'
n_users = 50
n_keywords = 50
n_layers = 3
n_docs = 30

# Reset keywords
Tag.objects.all().delete()

# 1. create users
Profile.objects.exclude(username='admin').exclude(username='AnonymousUser').delete()
create_users(n_users)

# 2. create documents
Document.objects.all().delete()
for d in range(0, n_docs):
    create_document(d)

# 3. create layers
# TODO

