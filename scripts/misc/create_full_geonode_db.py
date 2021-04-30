# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import sys
import os

from functools import partial
import glob
from random import randint
from timeit import Timer

from django.core.files import File
from django.contrib.auth import get_user_model

from taggit.models import Tag

from celery.exceptions import TimeoutError

from geonode.base.models import TopicCategory
from geonode.base.models import Region
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.layers.utils import file_upload
from geonode.layers.tasks import delete_layer


geonode_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '../geonode'))
sys.path.append(geonode_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


def get_random_user():
    """ Get a random user """
    users_count = get_user_model().objects.all().count()
    random_index = randint(0, users_count - 1)
    return get_user_model().objects.all()[random_index]


def assign_random_category(resource):
    """ Assign a random category to a resource """
    random_index = randint(0, TopicCategory.objects.all().count() - 1)
    tc = TopicCategory.objects.all()[random_index]
    resource.category = tc
    resource.save()


def assign_keywords(resource):
    """ Assigns up to 5 keywords to resource """
    for i in range(0, randint(0, 5)):
        resource.keywords.add(f'keyword_{randint(0, n_keywords)}')


def assign_regions(resource):
    """ Assign up to 5 regions to resource """
    for i in range(0, randint(0, 5)):
        random_index = randint(0, Region.objects.all().count() - 1)
        region = Region.objects.all()[random_index]
        resource.regions.add(region)


def create_users(n_users):
    """ Create n users in the database """
    for i in range(0, n_users):
        user = get_user_model()
        user.username = f'user_{i}'
        user.save()


def set_resource(resource):
    """ Assign poc, metadata_author, category and regions to resource """
    resource.poc = get_random_user()
    resource.metadata_author = get_random_user()
    assign_random_category(resource)
    assign_regions(resource)


def create_document(number):
    """ Creates a new document """
    file_list = glob.glob(f'{doc_path}*.jpg')
    random_index = randint(0, len(file_list) - 1)
    file_uri = file_list[random_index]
    title = f'Document N. {number}'
    img_filename = f'{number}_img.jpg'
    doc = Document(title=title, owner=get_random_user())
    doc.save()
    with open(file_uri, 'r') as f:
        img_file = File(f)
        doc.doc_file.save(img_filename, img_file, True)
    assign_keywords(doc)
    # regions
    resource = doc.get_self_resource()
    set_resource(resource)


def create_layer(number):
    """ Creates a new layer """
    file_list = glob.glob(f'{shp_path}*.shp')
    random_index = randint(0, len(file_list) - 1)
    file_uri = file_list[random_index]
    layer = file_upload(file_uri)
    # keywords
    assign_keywords(layer)
    # other stuff
    resource = layer.get_self_resource()
    set_resource(resource)


# in doc_path set a path containing *.jpg files
# in shp_path set a path containing *.shp files
doc_path = '/tmp/docs/'
shp_path = '/tmp/shp/'
n_users = 50
n_keywords = 100
n_layers = 500
n_docs = 500

# Reset keywords
Tag.objects.all().delete()

# 1. create users
get_user_model().objects.exclude(username='admin').exclude(username='AnonymousUser').delete()
create_users(n_users)

# 2. create documents
Document.objects.all().delete()
for d in range(0, n_docs):
    t = Timer(partial(create_document, d))
    print(f'Document {d} generated in: {t.timeit(number=1)}')

# 3. create layers
# first we delete layers
for layer in Layer.objects.all():
    result = delete_layer.apply_async((layer.id, ))

for l in range(0, n_layers):
    t = Timer(partial(create_layer, l))
    print(f'Layer {l} generated in: {t.timeit(number=1)}')
