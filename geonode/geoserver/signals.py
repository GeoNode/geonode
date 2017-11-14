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

import errno
import logging
import urllib

from urlparse import urlparse, urljoin

from django.utils.translation import ugettext
from django.conf import settings
from django.forms.models import model_to_dict


# use different name to avoid module clash
from geonode import geoserver as geoserver_app
from geonode.decorators import on_ogc_backend
from geonode.geoserver.ows import wcs_links, wfs_links, wms_links
from geonode.geoserver.helpers import cascading_delete, set_attributes_from_geoserver
from geonode.geoserver.helpers import set_styles, gs_catalog
from geonode.geoserver.helpers import ogc_server_settings
from geonode.geoserver.helpers import geoserver_upload
from geonode.geoserver.helpers import create_gs_thumbnail
from geonode.base.models import ResourceBase
from geonode.base.models import Link
from geonode.people.models import Profile
from geonode.layers.models import Layer
from geonode.social.signals import json_serializer_producer
from geonode.catalogue.models import catalogue_post_save

import geoserver
from geoserver.layer import Layer as GsLayer

logger = logging.getLogger("geonode.geoserver.signals")


def geoserver_delete(typename):
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        cascading_delete(gs_catalog, typename)


def geoserver_pre_delete(instance, sender, **kwargs):
    """Removes the layer from GeoServer
    """
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        if not getattr(instance, "service", None):
            if instance.alternate:
                cascading_delete(gs_catalog, instance.alternate)


def geoserver_pre_save(*args, **kwargs):
    # nothing to do here, processing is pushed to post-save
    pass


@on_ogc_backend(geoserver_app.BACKEND_PACKAGE)
def geoserver_post_save(instance, sender, **kwargs):
    from geonode.messaging import producer
    # this is attached to various models, (ResourceBase, Document)
    # so we should select what will be handled here
    if isinstance(instance, Layer):
        instance_dict = model_to_dict(instance)
        payload = json_serializer_producer(instance_dict)
        producer.geoserver_upload_layer(payload)


def geoserver_post_save_local(layer_id, *args, **kwargs):
    """Send information to geoserver.

       The attributes sent include:

        * Title
        * Abstract
        * Name
        * Keywords
        * Metadata Links,
        * Point of Contact name and url
    """
    # If it is a layer object, post process it. If not, abort.
    try:
        instance = Layer.objects.get(id=layer_id)
    except Layer.DoesNotExist as e:
        logger.exception(e)
        return
        # raise e

    # Don't run this signal if is a Layer from a remote service
    if getattr(instance, "service", None) is not None:
        return

    # Don't run this signal handler if it is a tile layer or a remote store (Service)
    #    Currently only gpkg files containing tiles will have this type & will be served via MapProxy.
    if hasattr(instance, 'storeType') and getattr(instance, 'storeType') in ['tileStore', 'remoteStore']:
        return instance

    gs_resource = None
    values = None

    # If the store in None then it's a new instance from an upload,
    # only in this case run the geoserver_upload method
    if not instance.store or getattr(instance, 'overwrite', False):
        base_file, info = instance.get_base_file()

        # There is no need to process it if there is not file.
        if base_file is None:
            return
        gs_name, workspace, values, gs_resource = geoserver_upload(instance,
                                                                   base_file.file.path,
                                                                   instance.owner,
                                                                   instance.name,
                                                                   overwrite=True,
                                                                   title=instance.title,
                                                                   abstract=instance.abstract,
                                                                   # keywords=instance.keywords,
                                                                   charset=instance.charset)

    if not gs_resource:
        gs_resource = gs_catalog.get_resource(
            instance.name,
            store=instance.store,
            workspace=instance.workspace)
        if not gs_resource:
            gs_resource = gs_catalog.get_resource(instance.alternate)

    if gs_resource:
        gs_resource.title = instance.title or ""
        gs_resource.abstract = instance.abstract or ""
        gs_resource.name = instance.name or ""

        if not values:
            values = dict(store=gs_resource.store.name,
                          storeType=gs_resource.store.resource_type,
                          alternate=gs_resource.store.workspace.name + ':' + gs_resource.name,
                          title=gs_resource.title or gs_resource.store.name,
                          abstract=gs_resource.abstract or '',
                          owner=instance.owner)
    else:
        return

    # Get metadata links
    metadata_links = []
    for link in instance.link_set.metadata():
        metadata_links.append((link.mime, link.name, link.url))

    gs_resource.metadata_links = metadata_links
    # gs_resource should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        try:
            gs_catalog.save(gs_resource)
        except geoserver.catalog.FailedRequestError as e:
            msg = ('Error while trying to save resource named %s in GeoServer, '
                   'try to use: "%s"' % (gs_resource, str(e)))
            e.args = (msg,)
            logger.exception(e)

    gs_layer = gs_catalog.get_layer(instance.name)

    if not gs_layer:
        gs_layer = gs_catalog.get_layer(instance.alternate)

    if gs_layer and instance.poc:
        # gsconfig now utilizes an attribution dictionary
        gs_layer.attribution = {'title': str(instance.poc),
                                'width': None,
                                'height': None,
                                'href': None,
                                'url': None,
                                'type': None}
        profile = Profile.objects.get(username=instance.poc.username)
        gs_layer.attribution_link = settings.SITEURL[
            :-1] + profile.get_absolute_url()
        # gs_layer should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            try:
                gs_catalog.save(gs_layer)
            except geoserver.catalog.FailedRequestError as e:
                msg = ('Error while trying to save layer named %s in GeoServer, '
                       'try to use: "%s"' % (gs_layer, str(e)))
                e.args = (msg,)
                logger.exception(e)

    if type(instance) is ResourceBase:
        if hasattr(instance, 'layer'):
            instance = instance.layer
        else:
            return

    if instance.storeType == "remoteStore":
        # Save layer attributes
        set_attributes_from_geoserver(instance)
        return

    """Get information from geoserver.

       The attributes retrieved include:

       * Bounding Box
       * SRID
       * Download links (WMS, WCS or WFS and KML)
       * Styles (SLD)
    """
    # instance.name = instance.name or gs_layer.name
    # instance.title = instance.title or gs_resource.title
    instance.abstract = gs_resource.abstract or ''
    instance.workspace = gs_resource.store.workspace.name
    instance.store = gs_resource.store.name

    bbox = gs_resource.latlon_bbox

    # FIXME(Ariel): Correct srid setting below
    # self.srid = gs_resource.src

    instance.srid_url = "http://www.spatialreference.org/ref/" + \
        instance.srid.replace(':', '/').lower() + "/"

    # Set bounding box values
    instance.bbox_x0 = bbox[0]
    instance.bbox_x1 = bbox[1]
    instance.bbox_y0 = bbox[2]
    instance.bbox_y1 = bbox[3]

    # Iterate over values from geoserver.
    for key in ['alternate', 'store', 'storeType']:
        # attr_name = key if 'typename' not in key else 'alternate'
        # print attr_name
        setattr(instance, key, values[key])

    if settings.RESOURCE_PUBLISHING:
        if instance.is_published != gs_resource.advertised:
            if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
                gs_resource.advertised = 'true' if instance.is_published else 'false'
                gs_catalog.save(gs_resource)

    if not settings.FREETEXT_KEYWORDS_READONLY:
        if gs_resource.keywords:
            for keyword in gs_resource.keywords:
                instance.keywords.add(keyword)

    if any(instance.keyword_list()):
        keywords = instance.keyword_list()
        if settings.FREETEXT_KEYWORDS_READONLY:
            if gs_resource.keywords:
                keywords += gs_resource.keywords
        gs_resource.keywords = list(set(keywords))

        # gs_resource should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            try:
                gs_catalog.save(gs_resource)
            except geoserver.catalog.FailedRequestError as e:
                msg = ('Error while trying to save resource named %s in GeoServer, '
                       'try to use: "%s"' % (gs_resource, str(e)))
                e.args = (msg,)
                logger.exception(e)

    to_update = {
        'title': instance.title or instance.name,
        'abstract': instance.abstract or "",
        'alternate': instance.alternate,
        'bbox_x0': instance.bbox_x0,
        'bbox_x1': instance.bbox_x1,
        'bbox_y0': instance.bbox_y0,
        'bbox_y1': instance.bbox_y1
    }

    # Update ResourceBase
    resources = ResourceBase.objects.filter(id=instance.resourcebase_ptr.id)
    resources.update(**to_update)

    # to_update['name'] = instance.name,
    to_update['workspace'] = instance.workspace
    to_update['store'] = instance.store
    to_update['storeType'] = instance.storeType
    to_update['typename'] = instance.alternate

    # Save all the modified information in the instance without triggering signals.
    Layer.objects.filter(id=instance.id).update(**to_update)

    # Refresh from DB
    instance.refresh_from_db()

    # store the resource to avoid another geoserver call in the post_save
    instance.gs_resource = gs_resource

    bbox = gs_resource.latlon_bbox
    dx = float(bbox[1]) - float(bbox[0])
    dy = float(bbox[3]) - float(bbox[2])

    dataAspect = 1 if dy == 0 else dx / dy

    height = 550
    width = int(height * dataAspect)

    # Set download links for WMS, WCS or WFS and KML
    links = wms_links(ogc_server_settings.public_url + 'wms?',
                      instance.alternate.encode('utf-8'), instance.bbox_string,
                      instance.srid, height, width)

    for ext, name, mime, wms_url in links:
        Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                   name=ugettext(name),
                                   defaults=dict(
                                       extension=ext,
                                       url=wms_url,
                                       mime=mime,
                                       link_type='image',
                                   )
                                   )

    if instance.storeType == "dataStore":
        links = wfs_links(
            ogc_server_settings.public_url +
            'wfs?',
            instance.alternate.encode('utf-8'))
        for ext, name, mime, wfs_url in links:
            if mime == 'SHAPE-ZIP':
                name = 'Zipped Shapefile'
            Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                       url=wfs_url,
                                       defaults=dict(
                                           extension=ext,
                                           name=name,
                                           mime=mime,
                                           url=wfs_url,
                                           link_type='data',
                                       )
                                       )

        gs_store_type = gs_resource.store.type.lower() if gs_resource.store.type else None
        geogig_repository = gs_resource.store.connection_parameters.get('geogig_repository', '')
        geogig_repo_name = geogig_repository.replace('geoserver://', '')

        if gs_store_type == 'geogig' and geogig_repo_name:

            repo_url = '{url}geogig/repos/{repo_name}'.format(
                url=ogc_server_settings.public_url,
                repo_name=geogig_repo_name)

            path = gs_resource.dom.findall('nativeName')

            if path:
                path = 'path={path}'.format(path=path[0].text)

            Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                       url=repo_url,
                                       defaults=dict(extension='html',
                                                     name='Clone in GeoGig',
                                                     mime='text/xml',
                                                     link_type='html'
                                                     )
                                       )

            def command_url(command):
                return "{repo_url}/{command}.json?{path}".format(repo_url=repo_url,
                                                                 path=path,
                                                                 command=command)

            Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                       url=command_url('log'),
                                       defaults=dict(extension='json',
                                                     name='GeoGig log',
                                                     mime='application/json',
                                                     link_type='html'
                                                     )
                                       )

            Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                       url=command_url('statistics'),
                                       defaults=dict(extension='json',
                                                     name='GeoGig statistics',
                                                     mime='application/json',
                                                     link_type='html'
                                                     )
                                       )

    elif instance.storeType == 'coverageStore':
        links = wcs_links(ogc_server_settings.public_url + 'wcs?',
                          instance.alternate.encode('utf-8'),
                          ','.join(str(x) for x in instance.bbox[0:4]),
                          instance.srid)

    for ext, name, mime, wcs_url in links:
        Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                   url=wcs_url,
                                   defaults=dict(
                                       extension=ext,
                                       name=name,
                                       mime=mime,
                                       link_type='data',
                                   )
                                   )

    kml_reflector_link_download = ogc_server_settings.public_url + "wms/kml?" + \
        urllib.urlencode({'layers': instance.alternate.encode('utf-8'), 'mode': "download"})

    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=kml_reflector_link_download,
                               defaults=dict(
                                   extension='kml',
                                   name="KML",
                                   mime='text/xml',
                                   link_type='data',
                               )
                               )

    kml_reflector_link_view = ogc_server_settings.public_url + "wms/kml?" + \
        urllib.urlencode({'layers': instance.alternate.encode('utf-8'), 'mode': "refresh"})

    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=kml_reflector_link_view,
                               defaults=dict(
                                   extension='kml',
                                   name="View in Google Earth",
                                   mime='text/xml',
                                   link_type='data',
                               )
                               )

    html_link_url = '%s%s' % (
        settings.SITEURL[:-1], instance.get_absolute_url())

    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=html_link_url,
                               defaults=dict(
                                   extension='html',
                                   name=instance.alternate,
                                   mime='text/html',
                                   link_type='html',
                               )
                               )

    logger.info("Creating Thumbnail for Layer [%s]" % (instance.alternate))
    create_gs_thumbnail(instance, overwrite=False)

    legend_url = ogc_server_settings.PUBLIC_LOCATION + \
        'wms?request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
        instance.alternate + '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'

    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=legend_url,
                               defaults=dict(
                                   extension='png',
                                   name='Legend',
                                   url=legend_url,
                                   mime='image/png',
                                   link_type='image',
                               )
                               )

    ogc_wms_path = '%s/wms' % instance.workspace
    ogc_wms_url = urljoin(ogc_server_settings.public_url, ogc_wms_path)
    ogc_wms_name = 'OGC WMS: %s Service' % instance.workspace
    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=ogc_wms_url,
                               defaults=dict(
                                   extension='html',
                                   name=ogc_wms_name,
                                   url=ogc_wms_url,
                                   mime='text/html',
                                   link_type='OGC:WMS',
                               )
                               )

    if instance.storeType == "dataStore":
        ogc_wfs_path = '%s/wfs' % instance.workspace
        ogc_wfs_url = urljoin(ogc_server_settings.public_url, ogc_wfs_path)
        ogc_wfs_name = 'OGC WFS: %s Service' % instance.workspace
        Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                   url=ogc_wfs_url,
                                   defaults=dict(
                                       extension='html',
                                       name=ogc_wfs_name,
                                       url=ogc_wfs_url,
                                       mime='text/html',
                                       link_type='OGC:WFS',
                                   )
                                   )

    if instance.storeType == "coverageStore":
        ogc_wcs_path = '%s/wcs' % instance.workspace
        ogc_wcs_url = urljoin(ogc_server_settings.public_url, ogc_wcs_path)
        ogc_wcs_name = 'OGC WCS: %s Service' % instance.workspace
        Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                   url=ogc_wcs_url,
                                   defaults=dict(
                                       extension='html',
                                       name=ogc_wcs_name,
                                       url=ogc_wcs_url,
                                       mime='text/html',
                                       link_type='OGC:WCS',
                                   )
                                   )

    # remove links that belong to and old address
    for link in instance.link_set.all():
        if not urlparse(
            settings.SITEURL).hostname == urlparse(
            link.url).hostname and not urlparse(
            ogc_server_settings.public_url).hostname == urlparse(
                link.url).hostname:
            link.delete()

    # Define the link after the cleanup, we should use this more rather then remove
    # potential parasites
    tile_url = ('%sgwc/service/gmaps?' % ogc_server_settings.public_url +
                'layers=%s' % instance.alternate.encode('utf-8') +
                '&zoom={z}&x={x}&y={y}' +
                '&format=image/png8'
                )

    link, created = Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                                               extension='tiles',
                                               name="Tiles",
                                               mime='image/png',
                                               link_type='image',
                                               )
    if created:
        Link.objects.filter(pk=link.pk).update(url=tile_url)

    # Save layer attributes
    set_attributes_from_geoserver(instance)

    # Save layer styles
    set_styles(instance, gs_catalog)

    # NOTTODO by simod: we should not do this!
    # need to be removed when fixing #2015
    catalogue_post_save(instance, Layer)


def geoserver_pre_save_maplayer(instance, sender, **kwargs):
    # If this object was saved via fixtures,
    # do not do post processing.
    if kwargs.get('raw', False):
        return

    try:
        instance.local = isinstance(
            gs_catalog.get_layer(
                instance.name),
            GsLayer)
    except EnvironmentError as e:
        if e.errno == errno.ECONNREFUSED:
            msg = 'Could not connect to catalog to verify if layer %s was local' % instance.name
            try:
                # HACK: The logger on signals throws an exception
                logger.warn(msg, e)
            except:
                pass
        else:
            raise e


def geoserver_post_save_map(instance, sender, **kwargs):
    instance.set_missing_info()
    create_gs_thumbnail(instance, overwrite=False)
