# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

import json
import os
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from pycsw import server
from geonode.catalogue.backends.pycsw_local import CONFIGURATION
from geonode.base.models import ResourceBase


@csrf_exempt
def csw_global_dispatch(request):
    """pycsw wrapper"""

    # this view should only operate if pycsw_local is the backend
    # else, redirect to the URL of the non-pycsw_local backend
    if settings.CATALOGUE['default']['ENGINE'] != 'geonode.catalogue.backends.pycsw_local':
        return HttpResponseRedirect(settings.CATALOGUE['default']['URL'])

    mdict = dict(settings.PYCSW['CONFIGURATION'], **CONFIGURATION)

    env = request.META.copy()
    env.update({'local.app_root': os.path.dirname(__file__),
                'REQUEST_URI': request.build_absolute_uri()})

    csw = server.Csw(mdict, env, version='2.0.2')

    content = csw.dispatch_wsgi()

    # pycsw 2.0 has an API break:
    # pycsw < 2.0: content = xml_response
    # pycsw >= 2.0: content = [http_status_code, content]
    # deal with the API break
    if isinstance(content, list):  # pycsw 2.0+
        content = content[1]

    return HttpResponse(content, content_type=csw.contenttype)


@csrf_exempt
def opensearch_dispatch(request):
    """OpenSearch wrapper"""

    ctx = {
        'shortname': settings.PYCSW['CONFIGURATION']['metadata:main']['identification_title'],
        'description': settings.PYCSW['CONFIGURATION']['metadata:main']['identification_abstract'],
        'developer': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_name'],
        'contact': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_email'],
        'attribution': settings.PYCSW['CONFIGURATION']['metadata:main']['provider_name'],
        'tags': settings.PYCSW['CONFIGURATION']['metadata:main']['identification_keywords'].replace(',', ' '),
        'url': settings.SITEURL.rstrip('/')
    }

    return render_to_response('catalogue/opensearch_description.xml', ctx,
                              content_type='application/opensearchdescription+xml')


@csrf_exempt
def data_json(request):
    """Return data.json representation of catalogue"""
    json_data = []
    for resource in ResourceBase.objects.all():
        record = {}
        record['title'] = resource.title
        record['description'] = resource.abstract
        record['keyword'] = resource.keyword_csv.split(',')
        record['modified'] = resource.csw_insert_date.isoformat()
        record['publisher'] = resource.poc.organization
        record['contactPoint'] = resource.poc.name_long
        record['mbox'] = resource.poc.email
        record['identifier'] = resource.uuid
        if resource.is_published:
            record['accessLevel'] = 'public'
        else:
            record['accessLevel'] = 'non-public'

        record['distribution'] = []
        for link in resource.link_set.all():
            record['distribution'].append({
                'accessURL': link.url,
                'format': link.mime
            })
        json_data.append(record)

    return HttpResponse(json.dumps(json_data), 'application/json')
