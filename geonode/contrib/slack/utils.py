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

import copy

from slugify import Slugify
from httplib import HTTPSConnection
from urlparse import urlsplit

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from .enumerations import SLACK_MESSAGE_TEMPLATES

from geonode.base.models import Link

custom_slugify = Slugify(separator='_')


def _build_state_resourcebase(resource):

    site = Site.objects.get_current()
    thumbnail_url = resource.get_thumbnail_url()
    owner_url = "{base}{context}".format(base=settings.SITEURL[:-1], context=resource.owner.get_absolute_url())

    state = {
        'title': resource.title,
        'type': resource.polymorphic_ctype,
        'sitename': site.name,
        'baseurl': settings.SITEURL,
        'owner_name': (resource.owner.get_full_name() or resource.owner.username),
        'owner_url': owner_url,
        'thumbnail_url': thumbnail_url
    }

    return state


def _build_state_layer(layer):

    state = _build_state_resourcebase(layer)

    url_detail = "{base}{context}".format(
        base=settings.SITEURL[:-1],
        context=reverse('layer_detail', args=(layer.service_typename,)))
    link_shp = Link.objects.get(resource=layer.get_self_resource(), name='Zipped Shapefile')
    link_geojson = Link.objects.get(resource=layer.get_self_resource(), name='GeoJSON')
    link_netkml = Link.objects.get(resource=layer.get_self_resource(), name='View in Google Earth')
    url_map = "{base}{context}".format(
        base=settings.SITEURL[:-1],
        context=reverse("new_map")+"?layer="+layer.service_typename)

    state['url_detail'] = url_detail
    state['url_shp'] = link_shp.url if link_shp else ''
    state['url_geojson'] = link_geojson.url if link_geojson else ''
    state['url_netkml'] = link_netkml.url if link_netkml else ''
    state['url_map'] = url_map

    return state


def _build_state_map(map):

    state = _build_state_resourcebase(map)

    url_detail = "{base}{context}".format(
        base=settings.SITEURL[:-1],
        context=reverse('map_detail', args=(map.id,)))
    url_view = "{base}{context}".format(
        base=settings.SITEURL[:-1],
        context=reverse('map_view', args=(map.id,)))
    url_download = "{base}{context}".format(
        base=settings.SITEURL[:-1],
        context=reverse('map_download', args=(map.id,)))

    state['url_detail'] = url_detail
    state['url_view'] = url_view
    state['url_download'] = url_download

    return state


def _build_state_document(document):

    state = _build_state_resourcebase(document)

    url_detail = "{base}{context}".format(
        base=settings.SITEURL[:-1],
        context=reverse('document_detail', args=(document.id,)))
    url_download = "{base}{context}".format(
        base=settings.SITEURL[:-1],
        context=reverse('document_download', args=(document.id,)))

    state['url_detail'] = url_detail
    state['url_download'] = url_download

    return state


def _render_attachment(a, state):

    for k in ["title", "title_link", "fallback", "text", "thumb_url"]:
        if k in a:
            a[k] = a[k].format(** state)

    if "fields" in a:
        for j in range(len(a["fields"])):
            f = a["fields"][j]
            if "title" in f:
                f["title"] = f["title"].format(** state)
            if "value" in f:
                f["value"] = f["value"].format(** state)
            a["fields"][j].update(f)

    return copy.deepcopy(a)


def _render_message_plain(template, resource):

    state = _build_state_resourcebase(resource)
    message = None
    try:
        message = {}
        if "text" in template:
            message["text"] = template["text"].format(** state)
        if "icon_url" in template:
            message["icon_url"] = template["icon_url"].format(** state)

    except:
        print "Could not build plain slack message for resource"
        message = None

    return message


def build_slack_message_layer(event, layer):

    message = None
    try:
        if event.lower() in SLACK_MESSAGE_TEMPLATES:
            event_lc = event.lower()
            if "attachments" in SLACK_MESSAGE_TEMPLATES[event_lc]:
                state = _build_state_layer(layer)
                message = copy.deepcopy(SLACK_MESSAGE_TEMPLATES[event_lc])
                for i in range(len(message["attachments"])):
                    a = _render_attachment(message["attachments"][i], state)
                    message["attachments"][i] = a

            else:
                message = _render_message_plain(SLACK_MESSAGE_TEMPLATES[event_lc], layer)
        else:
            print "Slack template not found."
    except:
        print "Could not build slack message for layer."
        message = None

    return message


def build_slack_message_map(event, map_obj):

    message = None
    try:
        if event.lower() in SLACK_MESSAGE_TEMPLATES:
            event_lc = event.lower()
            if "attachments" in SLACK_MESSAGE_TEMPLATES[event_lc]:
                state = _build_state_map(map_obj)
                message = copy.deepcopy(SLACK_MESSAGE_TEMPLATES[event_lc])
                for i in range(len(message["attachments"])):
                    a = _render_attachment(message["attachments"][i], state)
                    message["attachments"][i] = a

            else:
                message = _render_message_plain(SLACK_MESSAGE_TEMPLATES[event_lc], map_obj)
        else:
            print "Slack template not found."
    except:
        print "Could not build slack message for map."
        message = None

    return message


def build_slack_message_document(event, document):

    message = None
    try:
        if event.lower() in SLACK_MESSAGE_TEMPLATES:
            event_lc = event.lower()
            if "attachments" in SLACK_MESSAGE_TEMPLATES[event_lc]:
                state = _build_state_document(document)
                message = copy.deepcopy(SLACK_MESSAGE_TEMPLATES[event_lc])
                for i in range(len(message["attachments"])):
                    a = _render_attachment(message["attachments"][i], state)
                    message["attachments"][i] = a

            else:
                message = _render_message_plain(SLACK_MESSAGE_TEMPLATES[event_lc], document)
        else:
            print "Slack template not found."
    except:
        print "Could not build slack message for document."
        message = None

    return message


def send_slack_messages(message):
    if message and settings.SLACK_WEBHOOK_URLS:
        for url in settings.SLACK_WEBHOOK_URLS:
            _post_slack_message(message, url)
    else:
        print "Slack message is None."
        return None


def _post_slack_message(message, webhook_endpoint):

    url = urlsplit(webhook_endpoint)
    headers = {}
    conn = HTTPSConnection(url.hostname, url.port)
    conn.request("POST", str(url.path), json.dumps(message), headers)
    result = conn.getresponse()
    response = HttpResponse(
        result.read(),
        status=result.status,
        content_type=result.getheader("Content-Type", "text/plain"))
    return response
