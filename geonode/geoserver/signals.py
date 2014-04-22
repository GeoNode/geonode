import urllib
import logging
from datetime import datetime

from urlparse import urlparse, urljoin
from lxml import etree

from geonode.geoserver.helpers import cascading_delete
from gsimporter import Client
from geoserver.catalog import Catalog, FailedRequestError
from owslib.wcs import WebCoverageService
from geonode.geoserver.ows import wcs_links, wfs_links, wms_links, \
    wps_execute_layer_attribute_statistics

from geonode.utils import _user, _password, get_wms
from geonode.utils import http_client
from geonode.utils import ogc_server_settings
from geonode.layers.models import Layer, Attribute, Style
from geonode.base.models import Link

from geonode.people.models import Profile
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.enumerations import LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES
from geonode.base.models import Thumbnail

from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings

logger = logging.getLogger("geonode.geoserver.signals")

url = ogc_server_settings.rest
gs_catalog = Catalog(url, _user, _password)
gs_uploader = Client(url, _user, _password)
ogc_server_settings = ogc_server_settings
http_client = http_client

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
        gs_catalog = Catalog(url, _user, _password)
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


def set_styles(layer, gs_catalog):
    style_set = []
    gs_layer = gs_catalog.get_layer(layer.name)
    default_style = gs_layer.default_style
    layer.default_style = save_style(default_style)
    style_set.append(layer.default_style)

    alt_styles = gs_layer.styles

    for alt_style in alt_styles:
        style_set.append(save_style(alt_style))

    layer.styles = style_set
    return layer

def save_style(gs_style):
    style, created = Style.objects.get_or_create(name = gs_style.sld_name)
    style.sld_title = gs_style.sld_title
    style.sld_body = gs_style.sld_body
    style.sld_url = gs_style.body_href()
    style.save()
    return style


def is_layer_attribute_aggregable(store_type, field_name, field_type):
    """
    Decipher whether layer attribute is suitable for statistical derivation
    """

    # must be vector layer
    if store_type != 'dataStore':
        return False
    # must be a numeric data type
    if field_type not in LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES:
        return False
    # must not be an identifier type field
    if field_name.lower() in ['id', 'identifier']:
        return False

    return True


def get_attribute_statistics(layer_name, field):
    """
    Generate statistics (range, mean, median, standard deviation, unique values)
    for layer attribute
    """

    logger.debug('Deriving aggregate statistics for attribute %s', field)

    if not ogc_server_settings.WPS_ENABLED:
        return None
    try:
        return wps_execute_layer_attribute_statistics(layer_name, field)
    except Exception:
        logger.exception('Error generating layer aggregate statistics')


def get_coverage_grid_extent(instance):
    """
        Returns a list of integers with the size of the coverage
        extent in pixels
    """

    wcs = WebCoverageService(ogc_server_settings.public_url + 'wcs', '1.0.0')
    grid = wcs.contents[instance.workspace + ':' + instance.name].grid
    return [(int(h) - int(l) + 1) for
            h, l in zip(grid.highlimits, grid.lowlimits)]


def set_attributes(layer, overwrite=False):
    """
    Retrieve layer attribute names & types from Geoserver,
    then store in GeoNode database using Attribute model
    """
    attribute_map = []
    if layer.storeType == "dataStore":
        dft_url = ogc_server_settings.LOCATION + "wfs?" + urllib.urlencode({
            "service": "wfs",
            "version": "1.0.0",
            "request": "DescribeFeatureType",
            "typename": layer.typename.encode('utf-8'),
            })
        # The code below will fail if http_client cannot be imported
        body = http_client.request(dft_url)[1]
        doc = etree.fromstring(body)
        path = ".//{xsd}extension/{xsd}sequence/{xsd}element".format(xsd="{http://www.w3.org/2001/XMLSchema}")
        attribute_map = [[n.attrib["name"],n.attrib["type"]] for n in doc.findall(path)]

    elif layer.storeType == "coverageStore":
        dc_url = ogc_server_settings.LOCATION + "wcs?" + urllib.urlencode({
            "service": "wcs",
            "version": "1.1.0",
            "request": "DescribeCoverage",
            "identifiers": layer.typename.encode('utf-8')
        })
        try:
            response, body = http.request(dc_url)
            doc = etree.fromstring(body)
            path = ".//{wcs}Axis/{wcs}AvailableKeys/{wcs}Key".format(wcs="{http://www.opengis.net/wcs/1.1.1}")
            attribute_map = [[n.text,"raster"] for n in doc.findall(path)]
        except Exception:
            attribute_map = []

    attributes = layer.attribute_set.all()
    # Delete existing attributes if they no longer exist in an updated layer
    for la in attributes:
        lafound = False
        for field, ftype in attribute_map:
            if field == la.attribute:
                lafound = True
        if overwrite or not lafound:
            logger.debug("Going to delete [%s] for [%s]", la.attribute, layer.name.encode('utf-8'))
            la.delete()

    # Add new layer attributes if they don't already exist
    if attribute_map is not None:
        iter = len(Attribute.objects.filter(layer=layer)) + 1
        for field, ftype in attribute_map:
            if field is not None:
                la, created = Attribute.objects.get_or_create(layer=layer, attribute=field, attribute_type=ftype)
                if created:
                    if is_layer_attribute_aggregable(layer.storeType, field, ftype):
                        logger.debug("Generating layer attribute statistics")
                        result = get_attribute_statistics(layer.name, field)
                        if result is not None:
                            la.count = result['Count']
                            la.min = result['Min']
                            la.max = result['Max']
                            la.average = result['Average']
                            la.median = result['Median']
                            la.stddev = result['StandardDeviation']
                            la.sum = result['Sum']
                            la.unique_values = result['unique_values']
                            la.last_stats_updated = datetime.now()
                    la.attribute_label = field.title()
                    la.visible = ftype.find("gml:") != 0
                    la.display_order = iter
                    la.save()
                    iter += 1
                    logger.debug("Created [%s] attribute for [%s]", field, layer.name.encode('utf-8'))
    else:
        logger.debug("No attributes found")
