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

import json
import os
import logging
import xml.etree.ElementTree as ET
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from pycsw import server
from guardian.shortcuts import get_objects_for_user
from geonode.catalogue.backends.pycsw_local import CONFIGURATION
from geonode.base.models import ResourceBase
from geonode.layers.models import Layer
from geonode.base.models import ContactRole, SpatialRepresentationType
from geonode.people.models import Profile
from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext


@csrf_exempt
def csw_global_dispatch(request):
    """pycsw wrapper"""

    # this view should only operate if pycsw_local is the backend
    # else, redirect to the URL of the non-pycsw_local backend
    if settings.CATALOGUE['default']['ENGINE'] != 'geonode.catalogue.backends.pycsw_local':
        return HttpResponseRedirect(settings.CATALOGUE['default']['URL'])

    mdict = dict(settings.PYCSW['CONFIGURATION'], **CONFIGURATION)

    access_token = None
    if 'access_token' in request.session:
        access_token = request.session['access_token']

    absolute_uri = ('%s' % request.build_absolute_uri())
    query_string = ('%s' % request.META['QUERY_STRING'])

    if access_token and 'access_token' not in query_string:
        absolute_uri = ('%s&access_token=%s' % (absolute_uri, access_token))
        query_string = ('%s&access_token=%s' % (query_string, access_token))

    env = request.META.copy()
    env.update({'local.app_root': os.path.dirname(__file__),
                'REQUEST_URI': absolute_uri,
                'QUERY_STRING': query_string})

    if access_token:
        env.update({'access_token': access_token})

    # Save original filter before doing anything
    mdict_filter = mdict['repository']['filter']

    try:
        # Filter out Layers not accessible to the User
        authorized_ids = []
        if request.user:
            profiles = Profile.objects.filter(username=str(request.user))
        else:
            profiles = Profile.objects.filter(username="AnonymousUser")
        if profiles:
            authorized = list(get_objects_for_user(profiles[0], 'base.view_resourcebase').values('id'))
            layers = ResourceBase.objects.filter(id__in=[d['id'] for d in authorized])
            if layers:
                authorized_ids = [d['id'] for d in authorized]

        if len(authorized_ids) > 0:
            authorized_layers = "(" + (", ".join(str(e) for e in authorized_ids)) + ")"
            authorized_layers_filter = "id IN " + authorized_layers
            mdict['repository']['filter'] += " AND " + authorized_layers_filter
        else:
            authorized_layers_filter = "id = -9999"
            mdict['repository']['filter'] += " AND " + authorized_layers_filter

        # Filter out Documents and Maps
        if 'ALTERNATES_ONLY' in settings.CATALOGUE['default'] and settings.CATALOGUE['default']['ALTERNATES_ONLY']:
            mdict['repository']['filter'] += " AND alternate IS NOT NULL"

        # Filter out Layers belonging to specific Groups
        is_admin = False
        if request.user:
            is_admin = request.user.is_superuser if request.user else False

        if not is_admin and settings.GROUP_PRIVATE_RESOURCES:
            groups_ids = []
            if request.user:
                for group in request.user.groups.all():
                    groups_ids.append(group.id)

            if len(groups_ids) > 0:
                groups = "(" + (", ".join(str(e) for e in groups_ids)) + ")"
                groups_filter = "(group_id IS NULL OR group_id IN " + groups + ")"
                mdict['repository']['filter'] += " AND " + groups_filter
            else:
                groups_filter = "group_id IS NULL"
                mdict['repository']['filter'] += " AND " + groups_filter

        csw = server.Csw(mdict, env, version='2.0.2')

        content = csw.dispatch_wsgi()

        # pycsw 2.0 has an API break:
        # pycsw < 2.0: content = xml_response
        # pycsw >= 2.0: content = [http_status_code, content]
        # deal with the API break

        if isinstance(content, list):  # pycsw 2.0+
            content = content[1]

        spaces = {'csw': 'http://www.opengis.net/cat/csw/2.0.2',
                  'dc': 'http://purl.org/dc/elements/1.1/',
                  'dct': 'http://purl.org/dc/terms/',
                  'gmd': 'http://www.isotc211.org/2005/gmd',
                  'gml': 'http://www.opengis.net/gml',
                  'ows': 'http://www.opengis.net/ows',
                  'xs': 'http://www.w3.org/2001/XMLSchema',
                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                  'ogc': 'http://www.opengis.net/ogc',
                  'gco': 'http://www.isotc211.org/2005/gco',
                  'gmi': 'http://www.isotc211.org/2005/gmi'}

        for prefix, uri in spaces.iteritems():
            ET.register_namespace(prefix, uri)

        if access_token:
            tree = ET.fromstring(content)
            for online_resource in tree.findall('*//gmd:CI_OnlineResource', spaces):
                try:
                    linkage = online_resource.find('gmd:linkage', spaces)
                    for url in linkage.findall('gmd:URL', spaces):
                        if url.text:
                            if '?' not in url.text:
                                url.text += "?"
                            else:
                                url.text += "&"
                            url.text += ("access_token=%s" % (access_token))
                            url.set('updated', 'yes')
                except:
                    pass
            content = ET.tostring(tree, encoding='utf8', method='xml')
    finally:
        # Restore original filter before doing anything
        mdict['repository']['filter'] = mdict_filter

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


# transforms a row sql query into a two dimension array
def dictfetchall(cursor):
    """Returns all rows from a cursor as a dict"""
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


# choose separators
def get_CSV_spec_char():
    return {"separator": ';', "carriage_return": '\r\n'}


# format value to unicode str without ';' char
def fst(value):
    chrs = get_CSV_spec_char()
    return unicode(value).replace(chrs["separator"],
                                  ',').replace('\\n', ' ').replace('\r\n', ' ')


# from a resource object, build the corresponding metadata dict
# the aim is to handle the output format (csv, html or pdf) the same structure
def build_md_dict(resource):
    md_dict = {
        'r_uuid': {'label': 'uuid', 'value': resource.uuid},
        'r_title': {'label': 'titre', 'value': resource.title}
    }
    return md_dict


def get_keywords(resource):
    content = ' '
    cursor = connection.cursor()
    cursor.execute(
        "SELECT a.*,b.* FROM taggit_taggeditem as a,taggit_tag"
        " as b WHERE a.object_id = %s AND a.tag_id=b.id", [resource.id])
    struct_kw = dictfetchall(cursor)
    for x in struct_kw:
        content += fst(x['name']) + ', '
    return content[:-2]


# from a resource uuid, return a httpResponse
# containing the whole geonode metadata
@csrf_exempt
def csw_render_extra_format_txt(request, layeruuid, resname):
    """pycsw wrapper"""
    resource = ResourceBase.objects.get(uuid=layeruuid)
    chrs = get_CSV_spec_char()
    s = chrs['separator']
    c = chrs['carriage_return']
    sc = s + c
    content = 'Resource metadata' + sc
    content += 'uuid' + s + fst(resource.uuid) + sc
    content += 'title' + s + fst(resource.title) + sc
    content += 'resource owner' + s + fst(resource.owner) + sc
    content += 'date' + s + fst(resource.date) + sc
    content += 'date type' + s + fst(resource.date_type) + sc
    content += 'abstract' + s + fst(resource.abstract) + sc
    content += 'edition' + s + fst(resource.edition) + sc
    content += 'purpose' + s + fst(resource.purpose) + sc
    content += 'maintenance frequency' + s + fst(
                resource.maintenance_frequency) + sc

    try:
        sprt = SpatialRepresentationType.objects.get(
               id=resource.spatial_representation_type_id)
        content += 'identifier'+s+fst(sprt.identifier) + sc
    except ObjectDoesNotExist:
        content += 'ObjectDoesNotExist' + sc

    content += 'restriction code type' + s + fst(
                resource.restriction_code_type) + sc
    content += 'constraints other ' + s + fst(
                resource.constraints_other) + sc
    content += 'license' + s + fst(resource.license) + sc
    content += 'language' + s + fst(resource.language) + sc
    content += 'temporal extent' + sc
    content += 'temporal extent start' + s + fst(
                resource.temporal_extent_start) + sc
    content += 'temporal extent end' + s + fst(
                resource.temporal_extent_end) + sc
    content += 'supplemental information' + s + fst(
                resource.supplemental_information) + sc
    """content += 'URL de distribution ' + s + fst(
                resource.distribution_url) + sc"""
    """content += 'description de la distribution' + s + fst(
                resource.distribution_description) + sc"""
    content += 'data quality statement' + s + fst(
                resource.data_quality_statement) + sc
    content += 'extent ' + s + fst(resource.bbox_x0) + ',' + fst(
                resource.bbox_x1) + ',' + fst(
                resource.bbox_y0) + ',' + fst(resource.bbox_y1) + sc
    content += 'SRID  ' + s + fst(resource.srid) + sc
    content += 'Thumbnail url' + s + fst(resource.thumbnail_url) + sc

    content += 'keywords;' + get_keywords(resource) + s
    content += 'category' + s + fst(resource.category) + sc

    content += 'regions' + s
    for reg in resource.regions.all():
        content += fst(reg.name_en)+','
    content = content[:-1]
    content += sc

    if resource.detail_url.find('/layers/') > -1:
        layer = Layer.objects.get(resourcebase_ptr_id=resource.id)
        content += 'attribute data' + sc
        content += 'attribute name;label;description\n'
        for attr in layer.attribute_set.all():
            content += fst(attr.attribute) + s
            content += fst(attr.attribute_label) + s
            content += fst(attr.description) + sc

    pocr = ContactRole.objects.get(
           resource_id=resource.id, role='pointOfContact')
    pocp = Profile.objects.get(id=pocr.contact_id)
    content += "Point of Contact" + sc
    content += "name" + s + fst(pocp.last_name) + sc
    content += "e-mail" + s + fst(pocp.email) + sc

    logger = logging.getLogger(__name__)
    logger.error(content)

    # return render_to_response("/var/www/temp_download_md/test_3.txt")
    return HttpResponse(content.encode('utf-8').decode('utf-8'),
                        content_type="text/csv")


def csw_render_extra_format_html(request, layeruuid, resname):
    resource = ResourceBase.objects.get(uuid=layeruuid)
    extra_res_md = {}
    try:
        sprt = SpatialRepresentationType.objects.get(
               id=resource.spatial_representation_type_id)
        extra_res_md['sprt_identifier'] = sprt.identifier
    except ObjectDoesNotExist:
        extra_res_md['sprt_identifier'] = 'not filled'
    kw = get_keywords(resource)
    if len(kw) == 0:
        extra_res_md['keywords'] = "no keywords"
    else:
        extra_res_md['keywords'] = get_keywords(resource)

    if resource.detail_url.find('/layers/') > -1:
        layer = Layer.objects.get(resourcebase_ptr_id=resource.id)
        extra_res_md['atrributes'] = ''
        for attr in layer.attribute_set.all():
            extra_res_md['atrributes'] += '<tr>'
            extra_res_md['atrributes'] += '<td>' + unicode(
                                           attr.attribute) + '</td>'
            extra_res_md['atrributes'] += '<td>' + unicode(
                                           attr.attribute_label) + '</td>'
            extra_res_md['atrributes'] += '<td>' + unicode(
                                           attr.description) + '</td>'
            extra_res_md['atrributes'] += '</tr>'

    pocr = ContactRole.objects.get(
           resource_id=resource.id, role='pointOfContact')
    pocp = Profile.objects.get(id=pocr.contact_id)
    extra_res_md['poc_last_name'] = pocp.last_name
    extra_res_md['poc_email'] = pocp.email
    return render_to_response("geonode_metadata_full.html", RequestContext(
           request, {"resource": resource,
                     "extra_res_md": extra_res_md}))
