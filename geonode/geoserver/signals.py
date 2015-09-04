# -*- coding: utf-8 -*-
import errno
import logging
import urllib

from urlparse import urlparse, urljoin
from socket import error as socket_error

from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings

from geonode import GeoNodeException
from geonode.geoserver.ows import wcs_links, wfs_links, wms_links
from geonode.geoserver.helpers import cascading_delete, set_attributes
from geonode.geoserver.helpers import set_styles, gs_catalog, get_coverage_grid_extent
from geonode.geoserver.helpers import ogc_server_settings
from geonode.geoserver.helpers import geoserver_upload, http_client
from geonode.base.models import ResourceBase
from geonode.base.models import Link
from geonode.layers.utils import create_thumbnail
from geonode.people.models import Profile

from geoserver.layer import Layer as GsLayer

logger = logging.getLogger("geonode.geoserver.signals")


def geoserver_pre_delete(instance, sender, **kwargs):
    """Removes the layer from GeoServer
    """
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        if not getattr(instance, "service", None):
            cascading_delete(gs_catalog, instance.typename)


def geoserver_pre_save(instance, sender, **kwargs):
    """Send information to geoserver.

       The attributes sent include:

        * Title
        * Abstract
        * Name
        * Keywords
        * Metadata Links,
        * Point of Contact name and url
    """

    # Don't run this signal if is a Layer from a remote service
    if getattr(instance, "service", None) is not None:
        return

    gs_resource = None

    # If the store in None then it's a new instance from an upload,
    # only in this case run the geonode_uplaod method
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
        # Set fields obtained via the geoserver upload.
        instance.name = gs_name
        instance.workspace = workspace
        # Iterate over values from geoserver.
        for key in ['typename', 'store', 'storeType']:
            setattr(instance, key, values[key])

    if not gs_resource:
        gs_resource = gs_catalog.get_resource(
            instance.name,
            store=instance.store,
            workspace=instance.workspace)

    gs_resource.title = instance.title
    gs_resource.abstract = instance.abstract
    gs_resource.name = instance.name

    # Get metadata links
    metadata_links = []
    for link in instance.link_set.metadata():
        metadata_links.append((link.mime, link.name, link.url))

    gs_resource.metadata_links = metadata_links
    # gs_resource should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        gs_catalog.save(gs_resource)

    gs_layer = gs_catalog.get_layer(instance.name)

    if instance.poc and instance.poc:
        gs_layer.attribution = str(instance.poc)
        profile = Profile.objects.get(username=instance.poc.username)
        gs_layer.attribution_link = settings.SITEURL[
            :-1] + profile.get_absolute_url()
        # gs_layer should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            gs_catalog.save(gs_layer)

    """Get information from geoserver.

       The attributes retrieved include:

       * Bounding Box
       * SRID
       * Download links (WMS, WCS or WFS and KML)
       * Styles (SLD)
    """

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

    # store the resource to avoid another geoserver call in the post_save
    instance.gs_resource = gs_resource


def geoserver_post_save(instance, sender, **kwargs):
    """Save keywords to GeoServer

       The way keywords are implemented requires the layer
       to be saved to the database before accessing them.
    """

    if type(instance) is ResourceBase:
        if hasattr(instance, 'layer'):
            instance = instance.layer
        else:
            return

    if instance.storeType == "remoteStore":
        # Save layer attributes
        set_attributes(instance)
        return

    if not getattr(instance, 'gs_resource', None):
        try:
            gs_resource = gs_catalog.get_resource(
                instance.name,
                store=instance.store,
                workspace=instance.workspace)
        except socket_error as serr:
            if serr.errno != errno.ECONNREFUSED:
                # Not the error we are looking for, re-raise
                raise serr
            # If the connection is refused, take it easy.
            return
    else:
        gs_resource = instance.gs_resource

    if gs_resource is None:
        return

    if settings.RESOURCE_PUBLISHING:
        if instance.is_published != gs_resource.advertised:
            if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
                gs_resource.advertised = instance.is_published
                gs_catalog.save(gs_resource)

    if any(instance.keyword_list()):
        gs_resource.keywords = instance.keyword_list()
        # gs_resource should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            gs_catalog.save(gs_resource)

    bbox = gs_resource.latlon_bbox
    dx = float(bbox[1]) - float(bbox[0])
    dy = float(bbox[3]) - float(bbox[2])

    dataAspect = 1 if dy == 0 else dx / dy

    height = 550
    width = int(height * dataAspect)

    # Set download links for WMS, WCS or WFS and KML
    links = wms_links(ogc_server_settings.public_url + 'wms?',
                      instance.typename.encode('utf-8'), instance.bbox_string,
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
            instance.typename.encode('utf-8'))
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

        if gs_resource.store.type and gs_resource.store.type.lower() == 'geogig' and \
                gs_resource.store.connection_parameters.get('geogig_repository'):

            repo_url = '{url}geogig/{geogig_repository}'.format(
                url=ogc_server_settings.public_url,
                geogig_repository=gs_resource.store.connection_parameters.get('geogig_repository'))

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
        # FIXME(Ariel): This works for public layers, does it work for restricted too?
        # would those end up with no geotiff links, like, forever?
        permissions = instance.get_all_level_info()

        instance.set_permissions(
            {'users': {'AnonymousUser': ['view_resourcebase']}})

        try:
            # Potentially 3 dimensions can be returned by the grid if there is a z
            # axis.  Since we only want width/height, slice to the second
            # dimension
            covWidth, covHeight = get_coverage_grid_extent(instance)[:2]
        except GeoNodeException as e:
            msg = _('Could not create a download link for layer.')
            try:
                # HACK: The logger on signals throws an exception
                logger.warn(msg, e)
            except:
                pass
        else:

            links = wcs_links(ogc_server_settings.public_url + 'wcs?',
                              instance.typename.encode('utf-8'),
                              bbox=gs_resource.native_bbox[:-1],
                              crs=gs_resource.native_bbox[-1],
                              height=str(covHeight),
                              width=str(covWidth))

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

        instance.set_permissions(permissions)

    kml_reflector_link_download = ogc_server_settings.public_url + "wms/kml?" + \
        urllib.urlencode({'layers': instance.typename.encode('utf-8'), 'mode': "download"})

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
        urllib.urlencode({'layers': instance.typename.encode('utf-8'), 'mode': "refresh"})

    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=kml_reflector_link_view,
                               defaults=dict(
                                   extension='kml',
                                   name="View in Google Earth",
                                   mime='text/xml',
                                   link_type='data',
                               )
                               )

    tile_url = ('%sgwc/service/gmaps?' % ogc_server_settings.public_url +
                'layers=%s' % instance.typename.encode('utf-8') +
                '&zoom={z}&x={x}&y={y}' +
                '&format=image/png8'
                )

    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=tile_url,
                               defaults=dict(
                                   extension='tiles',
                                   name="Tiles",
                                   mime='image/png',
                                   link_type='image',
                               )
                               )

    html_link_url = '%s%s' % (
        settings.SITEURL[:-1], instance.get_absolute_url())

    Link.objects.get_or_create(resource=instance.resourcebase_ptr,
                               url=html_link_url,
                               defaults=dict(
                                   extension='html',
                                   name=instance.typename,
                                   mime='text/html',
                                   link_type='html',
                               )
                               )

    params = {
        'layers': instance.typename.encode('utf-8'),
        'format': 'image/png8',
        'width': 200,
        'height': 150,
    }

    # Avoid using urllib.urlencode here because it breaks the url.
    # commas and slashes in values get encoded and then cause trouble
    # with the WMS parser.
    p = "&".join("%s=%s" % item for item in params.items())

    thumbnail_remote_url = ogc_server_settings.PUBLIC_LOCATION + \
        "wms/reflect?" + p

    thumbnail_create_url = ogc_server_settings.LOCATION + \
        "wms/reflect?" + p

    create_thumbnail(instance, thumbnail_remote_url, thumbnail_create_url, ogc_client=http_client)

    legend_url = ogc_server_settings.PUBLIC_LOCATION + \
        'wms?request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
        instance.typename + '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'

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

    # Save layer attributes
    set_attributes(instance)

    # Save layer styles
    set_styles(instance, gs_catalog)
    # NOTTODO by simod: we should not do this!
    # need to be removed when fixing #2015
    from geonode.catalogue.models import catalogue_post_save
    from geonode.layers.models import Layer
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
    local_layers = []
    for layer in instance.layers:
        if layer.local:
            local_layers.append(layer.name)

    # If the map does not have any local layers, do not create the thumbnail.
    if len(local_layers) > 0:
        params = {
            'layers': ",".join(local_layers).encode('utf-8'),
            'format': 'image/png8',
            'width': 200,
            'height': 150,
        }

        # Add the bbox param only if the bbox is different to [None, None,
        # None, None]
        if None not in instance.bbox:
            params['bbox'] = instance.bbox_string

        # Avoid using urllib.urlencode here because it breaks the url.
        # commas and slashes in values get encoded and then cause trouble
        # with the WMS parser.
        p = "&".join("%s=%s" % item for item in params.items())

        thumbnail_remote_url = ogc_server_settings.PUBLIC_LOCATION + \
            "wms/reflect?" + p

        thumbnail_create_url = ogc_server_settings.LOCATION + \
            "wms/reflect?" + p

        create_thumbnail(instance, thumbnail_remote_url, thumbnail_create_url, check_bbox=False)
