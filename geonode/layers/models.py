# -*- coding: utf-8 -*-
import httplib2
import urllib
import logging
import sys
import uuid
import errno

from datetime import datetime
from lxml import etree

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from geonode import GeoNodeException
from geonode.utils import _wms, _user, _password, get_wms, bbox_to_wkt
from geonode.gs_helpers import cascading_delete
from geonode.people.models import Contact, Role 
from geonode.security.models import PermissionLevelMixin
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.ows import wcs_links, wfs_links, wms_links
from geonode.layers.enumerations import COUNTRIES, ALL_LANGUAGES, \
    UPDATE_FREQUENCIES, CONSTRAINT_OPTIONS, SPATIAL_REPRESENTATION_TYPES, \
    TOPIC_CATEGORIES, DEFAULT_SUPPLEMENTAL_INFORMATION, LINK_TYPES

from geoserver.catalog import Catalog
from taggit.managers import TaggableManager


logger = logging.getLogger("geonode.layers.models")


class LayerManager(models.Manager):
    
    def __init__(self):
        models.Manager.__init__(self)
        url = "%srest" % settings.GEOSERVER_BASE_URL
        self.gs_catalog = Catalog(url, _user, _password)


    def admin_contact(self):
        # this assumes there is at least one superuser
        superusers = User.objects.filter(is_superuser=True).order_by('id')
        if superusers.count() == 0:
            raise RuntimeError('GeoNode needs at least one admin/superuser set')
        
        contact = Contact.objects.get_or_create(user=superusers[0], 
                                                defaults={"name": "Geonode Admin"})[0]
        return contact

    def slurp(self, ignore_errors=True, verbosity=1, console=sys.stdout):
        """Configure the layers available in GeoServer in GeoNode.

           It returns a list of dictionaries with the name of the layer,
           the result of the operation and the errors and traceback if it failed.
        """
        if verbosity > 1:
            print >> console, "Inspecting the available layers in GeoServer ..."
        cat = self.gs_catalog
        resources = cat.get_resources()
        number = len(resources)
        if verbosity > 1:
            msg =  "Found %d layers, starting processing" % number
            print >> console, msg
        output = []
        for i, resource in enumerate(resources):
            name = resource.name
            store = resource.store
            workspace = store.workspace
            try:
                layer, created = Layer.objects.get_or_create(name=name, defaults = {
                    "workspace": workspace.name,
                    "store": store.name,
                    "storeType": store.resource_type,
                    "typename": "%s:%s" % (workspace.name, resource.name),
                    "title": resource.title or 'No title provided',
                    "abstract": resource.abstract or 'No abstract provided',
                    "uuid": str(uuid.uuid4())
                })

                layer.save()
            except Exception, e:
                if ignore_errors:
                    status = 'failed'
                    exception_type, error, traceback = sys.exc_info()
                else:
                    if verbosity > 0:
                        msg = "Stopping process because --ignore-errors was not set and an error was found."
                        print >> sys.stderr, msg
                    raise Exception('Failed to process %s' % resource.name, e), None, sys.exc_info()[2]
            else:
                if created:
                    layer.set_default_permissions()
                    status = 'created'
                else:
                    status = 'updated'

            msg = "[%s] Layer %s (%d/%d)" % (status, name, i+1, number)
            info = {'name': name, 'status': status}
            if status == 'failed':
                info['traceback'] = traceback
                info['exception_type'] = exception_type
                info['error'] = error
            output.append(info)
            if verbosity > 0:
                print >> console, msg
        return output


class Layer(models.Model, PermissionLevelMixin):
    """
    Layer Object loosely based on ISO 19115:2003
    """

    VALID_DATE_TYPES = [(x.lower(), _(x)) for x in ['Creation', 'Publication', 'Revision']]

    # internal fields
    objects = LayerManager()
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storeType = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    uuid = models.CharField(max_length=36)
    typename = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(User, blank=True, null=True)

    contacts = models.ManyToManyField(Contact, through='ContactRole')

    # section 1
    title = models.CharField(_('title'), max_length=255)
    date = models.DateTimeField(_('date'), default = datetime.now) # passing the method itself, not the result
    
    date_type = models.CharField(_('date type'), max_length=255, choices=VALID_DATE_TYPES, default='publication')

    edition = models.CharField(_('edition'), max_length=255, blank=True, null=True)
    abstract = models.TextField(_('abstract'), blank=True)
    purpose = models.TextField(_('purpose'), null=True, blank=True)
    maintenance_frequency = models.CharField(_('maintenance frequency'), max_length=255, choices = [(x, x) for x in UPDATE_FREQUENCIES], blank=True, null=True)

    # section 2
    # see poc property definition below

    # section 3
    keywords = TaggableManager(_('keywords'), blank=True, help_text=_("A space or comma-separated list of keywords"))
    keywords_region = models.CharField(_('keywords region'), max_length=3, choices= COUNTRIES, default = 'USA')
    constraints_use = models.CharField(_('constraints use'), max_length=255, choices = [(x, x) for x in CONSTRAINT_OPTIONS], default='copyright')
    constraints_other = models.TextField(_('constraints other'), blank=True, null=True)
    spatial_representation_type = models.CharField(_('spatial representation type'), max_length=255, choices=[(x,x) for x in SPATIAL_REPRESENTATION_TYPES], blank=True, null=True)

    # Section 4
    language = models.CharField(_('language'), max_length=3, choices=ALL_LANGUAGES, default='eng')
    topic_category = models.CharField(_('topic_category'), max_length=255, choices = [(x, x) for x in TOPIC_CATEGORIES], default = 'location')

    # Section 5
    temporal_extent_start = models.DateField(_('temporal extent start'), blank=True, null=True)
    temporal_extent_end = models.DateField(_('temporal extent end'), blank=True, null=True)

    supplemental_information = models.TextField(_('supplemental information'), default=DEFAULT_SUPPLEMENTAL_INFORMATION)

    # Section 6
    distribution_url = models.TextField(_('distribution URL'), blank=True, null=True)
    distribution_description = models.TextField(_('distribution description'), blank=True, null=True)

    # Section 8
    data_quality_statement = models.TextField(_('data quality statement'), blank=True, null=True)

    # Section 9
    # see metadata_author property definition below

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images and metadata records.
    bbox_x0 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    bbox_x1 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    bbox_y0 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    bbox_y1 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    srid = models.CharField(max_length=255, default='EPSG:4326')

    @property
    def bbox(self):
        return [self.bbox_x0, self.bbox_x1, self.bbox_y0, self.bbox_y1, self.srid]

    @property
    def bbox_string(self):
        return ",".join([str(self.bbox_x0), str(self.bbox_x1), str(self.bbox_y0), str(self.bbox_y1)])

    @property
    def geographic_bounding_box(self):
        return bbox_to_wkt(self.bbox_x0, self.bbox_x1, self.bbox_y0, self.bbox_y1, srid=self.srid )


    def eval_keywords_region(self):
        """Returns expanded keywords_region tuple'd value"""
        index = next((i for i,(k,v) in enumerate(COUNTRIES) if k==self.keywords_region),None)
        if index is not None:
            return COUNTRIES[index][1]
        else:
            return self.keywords_region

    def thumbnail(self):
        """ Generate a URL representing thumbnail of the resource """

        width = 20
        height = 20

        return settings.GEOSERVER_BASE_URL + "wms?" + urllib.urlencode({
            'service': 'WMS',
            'version': '1.1.1',
            'request': 'GetMap',
            'layers': self.typename,
            'format': 'image/png',
            'height': height,
            'width': width,
            'srs': self.srid,
            'bbox': self.bbox_string})

    def verify(self):
        """Makes sure the state of the layer is consistent in GeoServer and Catalogue.
        """
        
        # Check the layer is in the wms get capabilities record
        # FIXME: Implement caching of capabilities record site wide

        _local_wms = get_wms()
        record = _local_wms.contents.get(self.typename)
        if record is None:
            msg = "WMS Record missing for layer [%s]" % self.typename 
            raise GeoNodeException(msg)
        
    @property
    def attribute_names(self):
        if self.storeType == "dataStore":
            dft_url = settings.GEOSERVER_BASE_URL + "wfs?" + urllib.urlencode({
                    "service": "wfs",
                    "version": "1.0.0",
                    "request": "DescribeFeatureType",
                    "typename": self.typename
                })
            try:
                http = httplib2.Http()
                http.add_credentials(_user, _password)
                body = http.request(dft_url)[1]
                doc = etree.fromstring(body)
                path = ".//{xsd}extension/{xsd}sequence/{xsd}element".format(xsd="{http://www.w3.org/2001/XMLSchema}")
                atts = [n.attrib["name"] for n in doc.findall(path)]
            except Exception:
                atts = []
            return atts
        elif self.storeType == "coverageStore":
            dc_url = settings.GEOSERVER_BASE_URL + "wcs?" + urllib.urlencode({
                     "service": "wcs",
                     "version": "1.1.0",
                     "request": "DescribeCoverage",
                     "identifiers": self.typename
                })
            try:
                http = httplib2.Http()
                http.add_credentials(_user, _password)
                response, body = http.request(dc_url)
                doc = etree.fromstring(body)
                path = ".//{wcs}Axis/{wcs}AvailableKeys/{wcs}Key".format(wcs="{http://www.opengis.net/wcs/1.1.1}")
                atts = [n.text for n in doc.findall(path)]
            except Exception:
                atts = []
            return atts

    @property
    def display_type(self):
        return ({
            "dataStore" : "Vector Data",
            "coverageStore": "Raster Data",
        }).get(self.storeType, "Data")

    def delete_from_geoserver(self):
        cascading_delete(Layer.objects.gs_catalog, self.resource)

    @property
    def resource(self):
        if not hasattr(self, "_resource_cache"):
            cat = Layer.objects.gs_catalog
            try:
                ws = cat.get_workspace(self.workspace)
                store = cat.get_store(self.store, ws)
                self._resource_cache = cat.get_resource(self.name, store)
            except EnvironmentError, e:
                if e.errno == errno.ECONNREFUSED:
                    msg = ('Could not connect to geoserver at "%s"'
                           'to save information for layer "%s"' % (
                            settings.GEOSERVER_BASE_URL, self.name)
                          )
                    logger.warn(msg, e)
                    return None
                else:
                    raise e
        return self._resource_cache

    def _get_default_style(self):
        return self.publishing.default_style

    def _set_default_style(self, style):
        self.publishing.default_style = style

    default_style = property(_get_default_style, _set_default_style)

    def _get_styles(self):
        return self.publishing.styles

    def _set_styles(self, styles):
        self.publishing.styles = styles

    styles = property(_get_styles, _set_styles)
    
    @property
    def service_type(self):
        if self.storeType == 'coverageStore':
            return "WCS"
        if self.storeType == 'dataStore':
            return "WFS"

    @property
    def publishing(self):
        if not hasattr(self, "_publishing_cache"):
            cat = Layer.objects.gs_catalog
            self._publishing_cache = cat.get_layer(self.name)
        return self._publishing_cache

    @property
    def poc_role(self):
        role = Role.objects.get(value='pointOfContact')
        return role

    @property
    def metadata_author_role(self):
        role = Role.objects.get(value='author')
        return role

    def _set_poc(self, poc):
        # reset any poc asignation to this layer
        ContactRole.objects.filter(role=self.poc_role, layer=self).delete()
        #create the new assignation
        ContactRole.objects.create(role=self.poc_role, layer=self, contact=poc)

    def _get_poc(self):
        try:
            the_poc = ContactRole.objects.get(role=self.poc_role, layer=self).contact
        except ContactRole.DoesNotExist:
            the_poc = None
        return the_poc

    poc = property(_get_poc, _set_poc)

    def _set_metadata_author(self, metadata_author):
        # reset any metadata_author asignation to this layer
        ContactRole.objects.filter(role=self.metadata_author_role, layer=self).delete()
        #create the new assignation
        ContactRole.objects.create(role=self.metadata_author_role,
                                                  layer=self, contact=metadata_author)

    def _get_metadata_author(self):
        try:
            the_ma = ContactRole.objects.get(role=self.metadata_author_role, layer=self).contact
        except  ContactRole.DoesNotExist:
            the_ma = None
        return the_ma

    metadata_author = property(_get_metadata_author, _set_metadata_author)


    def keyword_list(self):
        return [kw.name for kw in self.keywords.all()]

    def get_absolute_url(self):
        return "/data/%s" % (self.typename)

    def __str__(self):
        return "%s Layer" % self.typename

    class Meta:
        # custom permissions,
        # change and delete are standard in django
        permissions = (('view_layer', 'Can view'), 
                       ('change_layer_permissions', "Can change permissions"), )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ  = 'layer_readonly'
    LEVEL_WRITE = 'layer_readwrite'
    LEVEL_ADMIN = 'layer_admin'
                 
    def set_default_permissions(self):
        self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ) 

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)

class ContactRole(models.Model):
    """
    ContactRole is an intermediate model to bind Contacts and Layers and apply roles.
    """
    contact = models.ForeignKey(Contact)
    layer = models.ForeignKey(Layer, null=True)
    role = models.ForeignKey(Role)

    def clean(self):
        """
        Make sure there is only one poc and author per layer
        """
        if (self.role == self.layer.poc_role) or (self.role == self.layer.metadata_author_role):
            contacts = self.layer.contacts.filter(contactrole__role=self.role)
            if contacts.count() == 1:
                # only allow this if we are updating the same contact
                if self.contact != contacts.get():
                    raise ValidationError('There can be only one %s for a given layer' % self.role)
        if self.contact.user is None:
            # verify that any unbound contact is only associated to one layer
            bounds = ContactRole.objects.filter(contact=self.contact).count()
            if bounds > 1:
                raise ValidationError('There can be one and only one layer linked to an unbound contact' % self.role)
            elif bounds == 1:
                # verify that if there was one already, it corresponds to this instace
                if ContactRole.objects.filter(contact=self.contact).get().id != self.id:
                    raise ValidationError('There can be one and only one layer linked to an unbound contact' % self.role)

    class Meta:
        unique_together = (("contact", "layer", "role"),)


class LinkManager(models.Manager):
    """Helper class to access links grouped by type
    """

    def data(self):
        return self.get_query_set().filter(link_type='data')

    def image(self):
        return self.get_query_set().filter(link_type='image')

    def download(self):
        return self.get_query_set().filter(link_type__in=['image', 'data'])

    def metadata(self):
        return self.get_query_set().filter(link_type='metadata')

    def original(self):
        return self.get_query_set().filter(link_type='original')
        


class Link(models.Model):
    """Auxiliary model for storying links for layers.

       This helps avoiding the need for runtime lookups
       to the OWS server or the CSW Catalogue.

       There are three types of links:
        * original: For uploaded files (shapefiles or geotiffs)
        * data: For WFS and WCS links that allow access to raw data
        * image: For WMS and TMS links
        * metadata: For CSW links
    """
    layer = models.ForeignKey(Layer)
    extension = models.CharField(max_length=255, help_text='For example "kml"')
    link_type = models.CharField(max_length=255, choices = [(x, x) for x in LINK_TYPES])
    name = models.CharField(max_length=255, help_text='For example "View in Google Earth"')
    mime = models.CharField(max_length=255, help_text='For example "text/xml"')
    url = models.URLField(unique=True)

    objects = LinkManager()


def geoserver_pre_delete(instance, sender, **kwargs): 
    """Removes the layer from GeoServer
    """
    instance.delete_from_geoserver()


def pre_save_layer(instance, sender, **kwargs):
    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'
    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    # Stay away from setting poc or metadata author in the usual way,
    # it requires the layer to be saved to the database.
    # By using contact_role_set we bypass that restriction.
    if instance.poc is None:
        instance.contactrole_set.create(role=instance.poc_role,
                                         contact=Layer.objects.admin_contact())

    if instance.metadata_author is None:
        instance.contactrole_set.create(role=instance.metadata_author_role,
                                         contact=Layer.objects.admin_contact())


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
    url = "%srest" % settings.GEOSERVER_BASE_URL
    try:
        gs_catalog = Catalog(url, _user, _password)
        gs_resource = gs_catalog.get_resource(instance.name)
    except EnvironmentError, e:
        gs_resource = None
        if e.errno == errno.ECONNREFUSED:
            msg = ('Could not connect to geoserver at "%s"'
                   'to save information for layer "%s"' % (
                    settings.GEOSERVER_BASE_URL, instance.name)
                  )
            logger.warn(msg, e)
            # If geoserver is not online, there is no need to continue
            return
        else:
            raise e

    gs_resource.title = instance.title
    gs_resource.abstract = instance.abstract
    gs_resource.name= instance.name

    # Get metadata links
    metadata_links = []
    for link in instance.link_set.metadata():
        metadata_links.append((link.name, link.mime, link.url))

    gs_resource.metadata_links = metadata_links
    gs_catalog.save(gs_resource)

    publishing = gs_catalog.get_layer(instance.name)
 
    if instance.poc and instance.poc.user:
        publishing.attribution = str(instance.poc.user)
        profile = Contact.objects.get(user=instance.poc.user)
        publishing.attribution_link = settings.SITEURL[:-1] + profile.get_absolute_url()
        gs_catalog.save(publishing)

    """Get information from geoserver.

       The attributes retrieved include:
       
       * Bounding Box
       * SRID
       * Download links (WMS, WCS or WFS and KML)
    """
    gs_resource = gs_catalog.get_resource(instance.name)

    bbox = gs_resource.latlon_bbox

    #FIXME(Ariel): Correct srid setting below
    #self.srid = gs_resource.src

    # Set bounding box values

    instance.bbox_x0 = bbox[0]
    instance.bbox_x1 = bbox[1]
    instance.bbox_y0 = bbox[2]
    instance.bbox_y1 = bbox[3]




def geoserver_post_save(instance, sender, **kwargs):
    """Save keywords to GeoServer

       The way keywords are implemented require the layer
       to be saved to the database before accessing them.
    """
    url = "%srest" % settings.GEOSERVER_BASE_URL

    try:
        gs_catalog = Catalog(url, _user, _password)
        gs_resource = gs_catalog.get_resource(instance.name)
    except EnvironmentError, e:
        if e.errno == errno.ECONNREFUSED:
            msg = ('Could not connect to geoserver at "%s"'
                   'to save information for layer "%s"' % (
                    settings.GEOSERVER_BASE_URL, instance.name)
                  )
            logger.warn(msg, e)
            # If geoserver is not online, there is no need to continue
            return
        else:
            raise e


    gs_resource.keywords = instance.keyword_list()
    gs_catalog.save(gs_resource)

    bbox = gs_resource.latlon_bbox
    dx = float(bbox[1]) - float(bbox[0])
    dy = float(bbox[3]) - float(bbox[2])

    dataAspect = 1 if dy == 0 else dx / dy

    height = 550
    width = int(height * dataAspect)

    # Set download links for WMS, WCS or WFS and KML

    links = wms_links(settings.GEOSERVER_BASE_URL + 'wms?',
                    instance.typename, instance.bbox_string,
                    instance.srid, height, width)

    for ext, name, mime, wms_url in links:
        instance.link_set.get_or_create(url=wms_url,
                          defaults=dict(
                            extension=ext,
                            name=name,
                            mime=mime,
                            link_type='image',
                           )
        )


    if instance.storeType == "dataStore":
        links = wfs_links(settings.GEOSERVER_BASE_URL + 'wfs?', instance.typename)
        for ext, name, mime, wfs_url in links:
            instance.link_set.get_or_create(url=wfs_url,
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
        links = wcs_links(settings.GEOSERVER_BASE_URL + 'wcs?', instance.typename)
        for ext, name, mime, wcs_url in links:
            instance.link_set.get_or_create(url=wcs_url,
                              defaults=dict(
                                extension=ext,
                                name=name,
                                mime=mime,
                                link_type='data',
                                )
                               )


    kml_reflector_link_download = settings.GEOSERVER_BASE_URL + "wms/kml?" + urllib.urlencode({
        'layers': instance.typename,
        'mode': "download"
    })

    instance.link_set.get_or_create(url=kml_reflector_link_download,
                       defaults=dict(
                        extension='kml',
                        name=_("KML"),
                        mime='text/xml',
                        link_type='data',
                        )
                       )

    kml_reflector_link_view = settings.GEOSERVER_BASE_URL + "wms/kml?" + urllib.urlencode({
        'layers': instance.typename,
        'mode': "refresh"
    })

    instance.link_set.get_or_create(url=kml_reflector_link_view,
                       defaults=dict(
                        extension='kml',
                        name=_("View in Google Earth"),
                        mime='text/xml',
                        link_type='data',
                        )
                       )



signals.pre_save.connect(pre_save_layer, sender=Layer)

signals.pre_save.connect(geoserver_pre_save, sender=Layer)
signals.pre_delete.connect(geoserver_pre_delete, sender=Layer)
signals.post_save.connect(geoserver_post_save, sender=Layer)
