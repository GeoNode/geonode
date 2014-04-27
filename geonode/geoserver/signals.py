import urllib
import logging

from urlparse import urlparse, urljoin

from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.files.base import ContentFile
from django.conf import settings

from geonode.geoserver.ows import wcs_links, wfs_links, wms_links
from geonode.geoserver.helpers import cascading_delete, set_attributes
from geonode.geoserver.helpers import _user, _password
from geonode.geoserver.helpers import set_styles, gs_catalog, get_coverage_grid_extent
from geonode.geoserver.helpers import ogc_server_settings
from geonode.utils import http_client
from geonode.base.models import Link
from geonode.base.models import Thumbnail
from geonode.layers.models import Layer
from geonode.people.models import Profile
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS

from geoserver.catalog import FailedRequestError
from geoserver.layer import Layer as GsLayer

logger = logging.getLogger("geonode.geoserver.signals")


def geoserver_pre_delete(instance, sender, **kwargs):
    """Removes the layer from GeoServer
    """
    #cascading_delete should only be called if ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings,"BACKEND_WRITE_ENABLED", True):
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
    url = ogc_server_settings.internal_rest
    try:
        gs_resource= gs_catalog.get_resource(instance.name,store=instance.store, workspace=instance.workspace)
    except (EnvironmentError, FailedRequestError) as e:
        gs_resource = None
        msg = ('Could not connect to geoserver at "%s"'
               'to save information for layer "%s"' % (
                ogc_server_settings.LOCATION, instance.name.encode('utf-8'))
              )
        logger.warn(msg, e)
        # If geoserver is not online, there is no need to continue
        return

    # If there is no resource returned it could mean one of two things:
    # a) There is a synchronization problem in geoserver
    # b) The unit tests are running and another geoserver is running in the
    # background.
    # For both cases it is sensible to stop processing the layer
    if gs_resource is None:
        logger.warn('Could not get geoserver resource for %s' % instance)
        return

    gs_resource.title = instance.title
    gs_resource.abstract = instance.abstract
    gs_resource.name= instance.name

    # Get metadata links
    metadata_links = []
    for link in instance.link_set.metadata():
        metadata_links.append((link.name, link.mime, link.url))

    gs_resource.metadata_links = metadata_links
    #gs_resource should only be called if ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings,"BACKEND_WRITE_ENABLED", True):
        gs_catalog.save(gs_resource)

    gs_layer = gs_catalog.get_layer(instance.name)

    if instance.poc and instance.poc.user:
        gs_layer.attribution = str(instance.poc.user)
        profile = Profile.objects.get(user=instance.poc.user)
        gs_layer.attribution_link = settings.SITEURL[:-1] + profile.get_absolute_url()
        #gs_layer should only be called if ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if getattr(ogc_server_settings,"BACKEND_WRITE_ENABLED", True):
            gs_catalog.save(gs_layer)

    """Get information from geoserver.

       The attributes retrieved include:

       * Bounding Box
       * SRID
       * Download links (WMS, WCS or WFS and KML)
       * Styles (SLD)
    """
    gs_resource= gs_catalog.get_resource(instance.name)

    bbox = gs_resource.latlon_bbox

    #FIXME(Ariel): Correct srid setting below
    #self.srid = gs_resource.src

    instance.srid_url = "http://www.spatialreference.org/ref/" + instance.srid.replace(':','/').lower() + "/"
    # Set bounding box values

    instance.bbox_x0 = bbox[0]
    instance.bbox_x1 = bbox[1]
    instance.bbox_y0 = bbox[2]
    instance.bbox_y1 = bbox[3]

    instance.thumbnail, created = Thumbnail.objects.get_or_create(resourcebase__id=instance.id)


def geoserver_post_save(instance, sender, **kwargs):
    """Save keywords to GeoServer

       The way keywords are implemented requires the layer
       to be saved to the database before accessing them.
    """
    url = ogc_server_settings.internal_rest

    try:
        gs_resource= gs_catalog.get_resource(instance.name)
    except (FailedRequestError, EnvironmentError) as e:
        msg = ('Could not connect to geoserver at "%s"'
               'to save information for layer "%s"' % (
                ogc_server_settings.LOCATION, instance.name.encode('utf-8'))
              )
        logger.warn(msg, e)
        # If geoserver is not online, there is no need to continue
        return

    # If there is no resource returned it could mean one of two things:
    # a) There is a synchronization problem in geoserver
    # b) The unit tests are running and another geoserver is running in the
    # background.
    # For both cases it is sensible to stop processing the layer
    if gs_resource is None:
        logger.warn('Could not get geoserver resource for %s' % instance)
        return

    gs_resource.keywords = instance.keyword_list()
    #gs_resource should only be called if ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings,"BACKEND_WRITE_ENABLED", True):
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
        Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        name=ugettext(name),
                        defaults=dict(
                            extension=ext,
                            url=wms_url,
                            mime=mime,
                            link_type='image',
                           )
                        )

    if instance.storeType == "dataStore":
        links = wfs_links(ogc_server_settings.public_url + 'wfs?', instance.typename.encode('utf-8'))
        for ext, name, mime, wfs_url in links:
            if mime=='SHAPE-ZIP':
                name = 'Zipped Shapefile'
            Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                            url=wfs_url,
                            defaults=dict(
                                extension=ext,
                                name=name,
                                mime=mime,
                                url=wfs_url,
                                link_type='data',
                            )
                        )

    elif instance.storeType == 'coverageStore':
        #FIXME(Ariel): This works for public layers, does it work for restricted too?
        # would those end up with no geotiff links, like, forever?
        permissions = {}
        permissions['anonymous'] = instance.get_gen_level(ANONYMOUS_USERS)
        permissions['authenticated'] = instance.get_gen_level(AUTHENTICATED_USERS)
        instance.set_gen_level(ANONYMOUS_USERS,'layer_readonly')

        #Potentially 3 dimensions can be returned by the grid if there is a z
        #axis.  Since we only want width/height, slice to the second dimension
        covWidth, covHeight = get_coverage_grid_extent(instance)[:2]
        links = wcs_links(ogc_server_settings.public_url + 'wcs?', instance.typename.encode('utf-8'),
                          bbox=gs_resource.native_bbox[:-1],
                          crs=gs_resource.native_bbox[-1],
                          height=str(covHeight), width=str(covWidth))
        for ext, name, mime, wcs_url in links:
            Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                                url=wcs_url,
                                defaults=dict(
                                    extension=ext,
                                    name=name,
                                    mime=mime,
                                    link_type='data',
                                )
                            )
                    
        instance.set_gen_level(ANONYMOUS_USERS,permissions['anonymous'])
        instance.set_gen_level(AUTHENTICATED_USERS,permissions['authenticated'])

    kml_reflector_link_download = ogc_server_settings.public_url + "wms/kml?" + urllib.urlencode({
        'layers': instance.typename.encode('utf-8'),
        'mode': "download"
    })

    Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=kml_reflector_link_download,
                        defaults=dict(
                            extension='kml',
                            name=_("KML"),
                            mime='text/xml',
                            link_type='data',
                        )
                    )

    kml_reflector_link_view = ogc_server_settings.public_url + "wms/kml?" + urllib.urlencode({
        'layers': instance.typename.encode('utf-8'),
        'mode': "refresh"
    })

    Link.objects.get_or_create(resource= instance.resourcebase_ptr,
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

    Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=tile_url,
                        defaults=dict(
                            extension='tiles',
                            name=_("Tiles"),
                            mime='image/png',
                            link_type='image',
                            )
                        )


    wms_path = '%s/%s/wms' % (instance.workspace, instance.name)
    ows_url = urljoin(ogc_server_settings.public_url, wms_path)

    Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=ows_url,
                        defaults=dict(
                            extension='html',
                            name=_("OWS"),
                            url=ows_url,
                            mime='text/html',
                            link_type='OGC:WMS',
                            )
                        )


    html_link_url = '%s%s' % (settings.SITEURL[:-1], instance.get_absolute_url())

    Link.objects.get_or_create(resource= instance.resourcebase_ptr,
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

    #Check if the bbox is invalid
    valid_x = (float(instance.bbox_x0) - float(instance.bbox_x1))**2 > 0
    valid_y = (float(instance.bbox_y1) - float(instance.bbox_y0))**2 > 0

    image = None

    if valid_x and valid_y:
        # Avoid using urllib.urlencode here because it breaks the url.
        # commas and slashes in values get encoded and then cause trouble
        # with the WMS parser.
        p = "&".join("%s=%s"%item for item in params.items())

        thumbnail_remote_url = ogc_server_settings.LOCATION + "wms/reflect?" + p

        Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=thumbnail_remote_url,
                        defaults=dict(
                            extension='png',
                            name=_("Remote Thumbnail"),
                            mime='image/png',
                            link_type='image',
                            )
                        )

        # Download thumbnail and save it locally.
        resp, image = http_client.request(thumbnail_remote_url)

        if 'ServiceException' in image or resp.status < 200 or resp.status > 299:
            msg = 'Unable to obtain thumbnail: %s' % image
            logger.debug(msg)
            # Replace error message with None.
            image = None

    if image is not None:
        if instance.has_thumbnail():
            instance.thumbnail.thumb_file.delete()

        instance.thumbnail.thumb_file.save('layer-%s-thumb.png' % instance.id, ContentFile(image))
        instance.thumbnail.thumb_spec = thumbnail_remote_url
        instance.thumbnail.save()

        thumbnail_url = urljoin(settings.SITEURL, instance.thumbnail.thumb_file.url)

        Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=thumbnail_url,
                        defaults=dict(
                            name=_('Thumbnail'),
                            extension='png',
                            mime='image/png',
                            link_type='image',
                            )
                        )

    ogc_wms_url = ogc_server_settings.public_url + 'wms?'
    Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=ogc_wms_url,
                        defaults=dict(
                            extension='html',
                            name=instance.name,
                            url=ogc_wms_url,
                            mime='text/html',
                            link_type='OGC:WMS',
                        )
                    )
                        
    if instance.storeType == "dataStore":
        ogc_wfs_url = ogc_server_settings.public_url + 'wfs?'
        Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                            url=ogc_wfs_url,
                            defaults=dict(
                                extension='html',
                                name=instance.name,
                                url=ogc_wfs_url,
                                mime='text/html',
                                link_type='OGC:WFS',
                            )
                        )

    if instance.storeType == "coverageStore":
        ogc_wcs_url = ogc_server_settings.public_url + 'wcs?'
        Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                            url=ogc_wcs_url,
                            defaults=dict(
                                extension='html',
                                name=instance.name,
                                url=ogc_wcs_url,
                                mime='text/html',
                                link_type='OGC:WCS',
                            )
                        )

    #remove links that belong to and old address

    for link in instance.link_set.all():
        if not urlparse(settings.SITEURL).hostname == urlparse(link.url).hostname and not \
                    urlparse(ogc_server_settings.public_url).hostname == urlparse(link.url).hostname:
            link.delete()

    #Save layer attributes
    set_attributes(instance)

    #Save layer styles
    set_styles(instance, gs_catalog)


def geoserver_pre_save_maplayer(instance, sender, **kwargs):
    # If this object was saved via fixtures,
    # do not do post processing.
    if kwargs.get('raw', False):
        return

    try:
        instance.local = isinstance(gs_catalog.get_layer(instance.name),GsLayer)
    except EnvironmentError, e:
        if e.errno == errno.ECONNREFUSED:
            msg = 'Could not connect to catalog to verify if layer %s was local' % instance.name
            logger.warn(msg, e)
        else:
            raise e


def geoserver_post_save_map(instance, sender, **kwargs):

    local_layers = []
    for layer in instance.layers:
        if layer.local:
            local_layers.append(Layer.objects.get(typename=layer.name).typename)

    params = {
        'layers': ",".join(local_layers).encode('utf-8'),
        'format': 'image/png8',
        'width': 200,
        'height': 150,
    }

    # Avoid using urllib.urlencode here because it breaks the url.
    # commas and slashes in values get encoded and then cause trouble
    # with the WMS parser.
    p = "&".join("%s=%s"%item for item in params.items())

    thumbnail_url = ogc_server_settings.LOCATION + "wms/reflect?" + p

    Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=thumbnail_url,
                        defaults=dict(
                            extension='png',
                            name=_("Remote Thumbnail"),
                            mime='image/png',
                            link_type='image',
                            )
                        )

    # Download thumbnail and save it locally.
    resp, image = http_client.request(thumbnail_url)

    if 'ServiceException' in image or resp.status < 200 or resp.status > 299:
        msg = 'Unable to obtain thumbnail: %s' % image
        logger.debug(msg)
        # Replace error message with None.
        image = None

    if image is not None:
        #Clean any orphan Thumbnail before
        Thumbnail.objects.filter(resourcebase__id=None).delete()
        thumbnail, created = Thumbnail.objects.get_or_create(resourcebase__id=instance.id)
        thumbnail.thumb_spec = thumbnail_url
        thumbnail.save_thumb(image, instance._thumbnail_path())

        Link.objects.get_or_create(resource= instance.resourcebase_ptr,
                        url=settings.SITEURL + instance._thumbnail_path(),
                        defaults=dict(
                            extension='png',
                            name=_("Thumbnail"),
                            mime='image/png',
                            link_type='image',
                            )
                        )
