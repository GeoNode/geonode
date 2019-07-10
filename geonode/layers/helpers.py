from collections import namedtuple, defaultdict
import datetime
from decimal import Decimal
import errno
from itertools import cycle, izip
import json
import logging
import traceback
import os
from os.path import basename, splitext, isfile
import re
import sys
from threading import local
import time
import uuid

import urllib
from urlparse import urlsplit, urlparse, urljoin

from agon_ratings.models import OverallRating
from bs4 import BeautifulSoup
from dialogos.models import Comment
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import pre_delete
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext as _
from geoserver.catalog import Catalog, FailedRequestError
from geoserver.resource import FeatureType, Coverage
from geoserver.store import CoverageStore, DataStore, datastore_from_index, \
    coveragestore_from_index, wmsstore_from_index
from geoserver.support import DimensionInfo
from geoserver.workspace import Workspace
from gsimporter import Client
from lxml import etree
from owslib.wcs import WebCoverageService
from owslib.wms import WebMapService
from geonode import GeoNodeException
from geonode.base.auth import get_or_create_token
from geonode.utils import http_client
from .models import Layer, Attribute, Style
from .enumerations import LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES
from geonode.security.views import _perms_info_json
from geonode.security.utils import set_geowebcache_invalidate_cache
import xml.etree.ElementTree as ET
from django.utils.module_loading import import_string
from geonode.geoserver.helpers import *

logger = logging.getLogger(__name__)








ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']

_wms = None
_csw = None
_user, _password = ogc_server_settings.credentials

url = ogc_server_settings.rest
gs_catalog = Catalog(url, _user, _password)
gs_uploader = Client(url, _user, _password)




def gs_slurp(
        ignore_errors=True,
        verbosity=1,
        console=None,
        owner=None,
        workspace=None,
        store=None,
        filter=None,
        skip_unadvertised=False,
        skip_geonode_registered=False,
        remove_deleted=False,
        permissions=None,
        execute_signals=False):
    """Configure the layers available in GeoServer in GeoNode.

       It returns a list of dictionaries with the name of the layer,
       the result of the operation and the errors and traceback if it failed.
    """
    if console is None:
        console = open(os.devnull, 'w')

    if verbosity > 0:
        print >> console, "Inspecting the available layers in GeoServer ..."
    cat = Catalog(ogc_server_settings.internal_rest, _user, _password)
    if workspace is not None:
        workspace = cat.get_workspace(workspace)
        if workspace is None:
            resources = []
        else:
            # obtain the store from within the workspace. if it exists, obtain resources
            # directly from store, otherwise return an empty list:
            if store is not None:
                store = get_store(cat, store, workspace=workspace)
                if store is None:
                    resources = []
                else:
                    resources = cat.get_resources(store=store)
            else:
                resources = cat.get_resources(workspace=workspace)

    elif store is not None:
        store = get_store(cat, store)
        resources = cat.get_resources(store=store)
    else:
        resources = cat.get_resources()
    if remove_deleted:
        resources_for_delete_compare = resources[:]
        workspace_for_delete_compare = workspace
        # filter out layers for delete comparison with GeoNode layers by following criteria:
        # enabled = true, if --skip-unadvertised: advertised = true, but
        # disregard the filter parameter in the case of deleting layers
        resources_for_delete_compare = [
            k for k in resources_for_delete_compare if k.enabled in ["true", True]]
        if skip_unadvertised:
            resources_for_delete_compare = [
                k for k in resources_for_delete_compare if k.advertised in ["true", True]]

    if filter:
        resources = [k for k in resources if filter in k.name]

    # filter out layers depending on enabled, advertised status:
    resources = [k for k in resources if k.enabled in ["true", True]]
    if skip_unadvertised:
        resources = [k for k in resources if k.advertised in ["true", True]]

    # filter out layers already registered in geonode
    layer_names = Layer.objects.all().values_list('alternate', flat=True)
    if skip_geonode_registered:
        resources = [k for k in resources
                     if not '%s:%s' % (k.workspace.name, k.name) in layer_names]

    # TODO: Should we do something with these?
    # i.e. look for matching layers in GeoNode and also disable?
    # disabled_resources = [k for k in resources if k.enabled == "false"]

    number = len(resources)
    if verbosity > 0:
        msg = "Found %d layers, starting processing" % number
        print >> console, msg
    output = {
        'stats': {
            'failed': 0,
            'updated': 0,
            'created': 0,
            'deleted': 0,
        },
        'layers': [],
        'deleted_layers': []
    }
    start = datetime.datetime.now(timezone.get_current_timezone())
    for i, resource in enumerate(resources):
        name = resource.name
        the_store = resource.store
        workspace = the_store.workspace
        try:
            layer, created = Layer.objects.get_or_create(name=name, workspace=workspace.name, defaults={
                # "workspace": workspace.name,
                "store": the_store.name,
                "storeType": the_store.resource_type,
                "alternate": "%s:%s" % (workspace.name.encode('utf-8'), resource.name.encode('utf-8')),
                "title": resource.title or 'No title provided',
                "abstract": resource.abstract or unicode(_('No abstract provided')).encode('utf-8'),
                "owner": owner,
                "uuid": str(uuid.uuid4()),
                "bbox_x0": Decimal(resource.native_bbox[0]),
                "bbox_x1": Decimal(resource.native_bbox[1]),
                "bbox_y0": Decimal(resource.native_bbox[2]),
                "bbox_y1": Decimal(resource.native_bbox[3]),
                "srid": resource.projection
            })

            # sync permissions in GeoFence
            perm_spec = json.loads(_perms_info_json(layer))
            layer.set_permissions(perm_spec)

            # recalculate the layer statistics
            set_attributes_from_geoserver(layer, overwrite=True)

            # in some cases we need to explicitily save the resource to execute the signals
            # (for sure when running updatelayers)
            if execute_signals:
                layer.save()

            # Fix metadata links if the ip has changed
            if layer.link_set.metadata().count() > 0:
                if not created and settings.SITEURL not in layer.link_set.metadata()[0].url:
                    layer.link_set.metadata().delete()
                    layer.save()
                    metadata_links = []
                    for link in layer.link_set.metadata():
                        metadata_links.append((link.mime, link.name, link.url))
                    resource.metadata_links = metadata_links
                    cat.save(resource)

        except Exception as e:
            if ignore_errors:
                status = 'failed'
                exception_type, error, traceback = sys.exc_info()
            else:
                if verbosity > 0:
                    msg = "Stopping process because --ignore-errors was not set and an error was found."
                    print >> sys.stderr, msg
                raise Exception(
                    'Failed to process %s' %
                    resource.name.encode('utf-8'), e), None, sys.exc_info()[2]
        else:
            if created:
                if not permissions:
                    layer.set_default_permissions()
                else:
                    layer.set_permissions(permissions)

                status = 'created'
                output['stats']['created'] += 1
            else:
                status = 'updated'
                output['stats']['updated'] += 1

        msg = "[%s] Layer %s (%d/%d)" % (status, name, i + 1, number)
        info = {'name': name, 'status': status}
        if status == 'failed':
            output['stats']['failed'] += 1
            info['traceback'] = traceback
            info['exception_type'] = exception_type
            info['error'] = error
        output['layers'].append(info)
        if verbosity > 0:
            print >> console, msg

    if remove_deleted:
        q = Layer.objects.filter()
        if workspace_for_delete_compare is not None:
            if isinstance(workspace_for_delete_compare, Workspace):
                q = q.filter(
                    workspace__exact=workspace_for_delete_compare.name)
            else:
                q = q.filter(workspace__exact=workspace_for_delete_compare)
        if store is not None:
            if isinstance(
                    store,
                    CoverageStore) or isinstance(
                    store,
                    DataStore):
                q = q.filter(store__exact=store.name)
            else:
                q = q.filter(store__exact=store)
        logger.debug("Executing 'remove_deleted' logic")
        logger.debug("GeoNode Layers Found:")

        # compare the list of GeoNode layers obtained via query/filter with valid resources found in GeoServer
        # filtered per options passed to updatelayers: --workspace, --store, --skip-unadvertised
        # add any layers not found in GeoServer to deleted_layers (must match
        # workspace and store as well):
        deleted_layers = []
        for layer in q:
            logger.debug(
                "GeoNode Layer info: name: %s, workspace: %s, store: %s",
                layer.name,
                layer.workspace,
                layer.store)
            layer_found_in_geoserver = False
            for resource in resources_for_delete_compare:
                # if layer.name matches a GeoServer resource, check also that
                # workspace and store match, mark valid:
                if layer.name == resource.name:
                    if layer.workspace == resource.workspace.name and layer.store == resource.store.name:
                        logger.debug(
                            "Matches GeoServer layer: name: %s, workspace: %s, store: %s",
                            resource.name,
                            resource.workspace.name,
                            resource.store.name)
                        layer_found_in_geoserver = True
            if not layer_found_in_geoserver:
                logger.debug(
                    "----- Layer %s not matched, marked for deletion ---------------",
                    layer.name)
                deleted_layers.append(layer)

        number_deleted = len(deleted_layers)
        if verbosity > 0:
            msg = "\nFound %d layers to delete, starting processing" % number_deleted if number_deleted > 0 else \
                "\nFound %d layers to delete" % number_deleted
            print >> console, msg

        for i, layer in enumerate(deleted_layers):
            logger.debug(
                "GeoNode Layer to delete: name: %s, workspace: %s, store: %s",
                layer.name,
                layer.workspace,
                layer.store)
            try:
                # delete ratings, comments, and taggit tags:
                ct = ContentType.objects.get_for_model(layer)
                OverallRating.objects.filter(
                    content_type=ct,
                    object_id=layer.id).delete()
                Comment.objects.filter(
                    content_type=ct,
                    object_id=layer.id).delete()
                layer.keywords.clear()

                layer.delete()
                output['stats']['deleted'] += 1
                status = "delete_succeeded"
            except Exception as e:
                status = "delete_failed"
            finally:
                from .signals import geoserver_pre_delete
                pre_delete.connect(geoserver_pre_delete, sender=Layer)

            msg = "[%s] Layer %s (%d/%d)" % (status,
                                             layer.name,
                                             i + 1,
                                             number_deleted)
            info = {'name': layer.name, 'status': status}
            if status == "delete_failed":
                exception_type, error, traceback = sys.exc_info()
                info['traceback'] = traceback
                info['exception_type'] = exception_type
                info['error'] = error
            output['deleted_layers'].append(info)
            if verbosity > 0:
                print >> console, msg

    finish = datetime.datetime.now(timezone.get_current_timezone())
    td = finish - start
    output['stats']['duration_sec'] = td.microseconds / \
        1000000 + td.seconds + td.days * 24 * 3600
    return output


