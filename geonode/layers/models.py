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
from urlparse import urlparse

import httplib2
import urllib
import logging
import sys
import uuid
import errno

from datetime import datetime
from lxml import etree
from urlparse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from geonode import GeoNodeException
from geonode.utils import _wms, _user, _password, get_wms, bbox_to_wkt
from geonode.gs_helpers import cascading_delete
from geonode.people.models import Profile, Role
from geonode.security.models import PermissionLevelMixin
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.ows import wcs_links, wfs_links, wms_links
from geonode.layers.enumerations import COUNTRIES, ALL_LANGUAGES, \
    HIERARCHY_LEVELS, UPDATE_FREQUENCIES, CONSTRAINT_OPTIONS, \
    SPATIAL_REPRESENTATION_TYPES,  TOPIC_CATEGORIES, \
    DEFAULT_SUPPLEMENTAL_INFORMATION, LINK_TYPES

from geoserver.catalog import Catalog, FailedRequestError
from taggit.managers import TaggableManager
from agon_ratings.models import OverallRating

logger = logging.getLogger("geonode.layers.models")

def get_default_category():
    return TopicCategory.objects.get(slug='location')

class Style(models.Model):
    """Model for storing styles.
    """
    name = models.CharField(_('style name'), max_length=255, unique=True)
    sld_title = models.CharField(max_length=255, null=True, blank=True)
    sld_body = models.TextField(_('sld text'), null=True, blank=True)
    sld_version = models.CharField(_('sld version'), max_length=12, null=True, blank=True)
    sld_url = models.CharField(_('sld url'), null = True, max_length=1000)
    workspace = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "%s" % self.name


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

        contact = Profile.objects.get_or_create(user=superusers[0],
                                                defaults={"name": "Geonode Admin"})[0]
        return contact


class TopicCategory(models.Model):

    name = models.CharField(max_length=50)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    def __unicode__(self):
        return u"{0}".format(self.name)

    class Meta:
        ordering = ("name",)


class ResourceBase(models.Model, PermissionLevelMixin):
    """
    Base Resource Object loosely based on ISO 19115:2003
    """

    VALID_DATE_TYPES = [(x.lower(), _(x)) for x in ['Creation', 'Publication', 'Revision']]

    # internal fields
    uuid = models.CharField(max_length=36)
    owner = models.ForeignKey(User, blank=True, null=True)

    # section 1
    title = models.CharField(_('title'), max_length=255, help_text=_('name by which the cited resource is known'))
    date = models.DateTimeField(_('date'), default = datetime.now, help_text=_('reference date for the cited resource')) # passing the method itself, not the result

    date_type = models.CharField(_('date type'), max_length=255, choices=VALID_DATE_TYPES, default='publication', help_text=_('identification of when a given event occurred'))

    edition = models.CharField(_('edition'), max_length=255, blank=True, null=True, help_text=_('version of the cited resource'))
    abstract = models.TextField(_('abstract'), blank=True, help_text=_('brief narrative summary of the content of the resource(s)'))
    purpose = models.TextField(_('purpose'), null=True, blank=True, help_text=_('summary of the intentions with which the resource(s) was developed'))

    maintenance_frequency = models.CharField(_('maintenance frequency'), max_length=255, choices=UPDATE_FREQUENCIES, blank=True, null=True, help_text=_('frequency with which modifications and deletions are made to the data after it is first produced'))

    # section 2
    # see poc property definition below

    # section 3
    keywords = TaggableManager(_('keywords'), blank=True, help_text=_('commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject (space or comma-separated'))
    keywords_region = models.CharField(_('keywords region'), max_length=3, choices=COUNTRIES, default='USA', help_text=_('keyword identifies a location'))
    constraints_use = models.CharField(_('constraints use'), max_length=255, choices=[(x, x) for x in CONSTRAINT_OPTIONS], default='copyright', help_text=_('constraints applied to assure the protection of privacy or intellectual property, and any special restrictions or limitations or warnings on using the resource or metadata'))
    constraints_other = models.TextField(_('constraints other'), blank=True, null=True, help_text=_('other restrictions and legal prerequisites for accessing and using the resource or metadata'))
    spatial_representation_type = models.CharField(_('spatial representation type'), max_length=255, choices=SPATIAL_REPRESENTATION_TYPES, blank=True, null=True, help_text=_('method used to represent geographic information in the dataset'))

    # Section 4
    language = models.CharField(_('language'), max_length=3, choices=ALL_LANGUAGES, default='eng', help_text=_('language used within the dataset'))
    topic_category = models.CharField(_('topic_category'), editable=False, max_length=255, choices=TOPIC_CATEGORIES, default='location')
    category = models.ForeignKey(TopicCategory, help_text=_('high-level geographic data thematic classification to assist in the grouping and search of available geographic data sets.'), null=True, blank=True, default=get_default_category)

    # Section 5
    temporal_extent_start = models.DateField(_('temporal extent start'), blank=True, null=True, help_text=_('time period covered by the content of the dataset (start)'))
    temporal_extent_end = models.DateField(_('temporal extent end'), blank=True, null=True, help_text=_('time period covered by the content of the dataset (end)'))

    supplemental_information = models.TextField(_('supplemental information'), default=DEFAULT_SUPPLEMENTAL_INFORMATION, help_text=_('any other descriptive information about the dataset'))

    # Section 6
    distribution_url = models.TextField(_('distribution URL'), blank=True, null=True, help_text=_('information about on-line sources from which the dataset, specification, or community profile name and extended metadata elements can be obtained'))
    distribution_description = models.TextField(_('distribution description'), blank=True, null=True, help_text=_('detailed text description of what the online resource is/does'))

    # Section 8
    data_quality_statement = models.TextField(_('data quality statement'), blank=True, null=True, help_text=_('general explanation of the data producer\'s knowledge about the lineage of a dataset'))

    # Section 9
    # see metadata_author property definition below

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images and metadata records.
    bbox_x0 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    bbox_x1 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    bbox_y0 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    bbox_y1 = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    srid = models.CharField(max_length=255, default='EPSG:4326')

    # CSW specific fields
    csw_typename = models.CharField(_('CSW typename'), max_length=32, default='gmd:MD_Metadata', null=False)
    csw_schema = models.CharField(_('CSW schema'), max_length=64, default='http://www.isotc211.org/2005/gmd', null=False)
    csw_mdsource = models.CharField(_('CSW source'), max_length=256, default='local', null=False)
    csw_insert_date = models.DateTimeField(_('CSW insert date'), auto_now_add=True, null=True)
    csw_type = models.CharField(_('CSW type'), max_length=32, default='dataset', null=False, choices=HIERARCHY_LEVELS)
    csw_anytext = models.TextField(_('CSW anytext'), null=True)
    csw_wkt_geometry = models.TextField(_('CSW WKT geometry'), null=False, default='SRID=4326;POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))')

    # metadata XML specific fields
    metadata_uploaded = models.BooleanField(default=False)
    metadata_xml = models.TextField(null=True, default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>', blank=True)

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

    @property
    def poc_role(self):
        role = Role.objects.get(value='pointOfContact')
        return role

    @property
    def metadata_author_role(self):
        role = Role.objects.get(value='author')
        return role

    def keyword_list(self):
        return [kw.name for kw in self.keywords.all()]

    @property
    def keyword_csv(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return ','.join([kw.name for kw in keywords_qs])
        else:
            return ''
            
    def class_name(value): 
        return value.__class__.__name__ 

    class Meta:
        abstract = True


def add_bbox_query(q, bbox):
    '''modify the queryset q to limit to the provided bbox

    bbox - 4 tuple of floats representing x0,x1,y0,y1
    returns the modified query
    '''
    bbox = map(str, bbox) # 2.6 compat - float to decimal conversion
    q = q.filter(bbox_x0__gte=bbox[0])
    q = q.filter(bbox_x1__lte=bbox[1])
    q = q.filter(bbox_y0__gte=bbox[2])
    return q.filter(bbox_y1__lte=bbox[3])


class Layer(ResourceBase):
    """
    Layer (inherits ResourceBase fields)
    """

    # internal fields
    objects = LayerManager()
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storeType = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    typename = models.CharField(max_length=128, unique=True)

    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    contacts = models.ManyToManyField(Profile, through='ContactRole')

    default_style = models.ForeignKey(Style, related_name='layer_default_style', null=True, blank=True)
    styles = models.ManyToManyField(Style, related_name='layer_styles')

    def download_links(self):
        links = []
        for url in self.link_set.all():
            description = '%s (%s Format)' % (self.title, url.name)
            links.append((self.title, description, 'WWW:DOWNLOAD-1.0-http--download', url.url))
        abs_url = '%s%s' % (settings.SITEURL[:-1], self.get_absolute_url())
        links.append((self.title, self.title, 'WWW:LINK-1.0-http--link', abs_url))
        return links

    def thumbnail(self, width=20, height=None):
        """ Generate a URL representing thumbnail of the layer """

        params = {
            'layers': self.typename,
            'format': 'image/png8',
            'width': width,
        }
        if height is not None:
            params['height'] = height

        # Avoid usring urllib.urlencode here because it breaks the url.
        # commas and slashes in values get encoded and then cause trouble
        # with the WMS parser.
        p = "&".join("%s=%s"%item for item in params.items())

        return settings.GEOSERVER_BASE_URL + "wms/reflect?" + p


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
    def display_type(self):
        return ({
            "dataStore" : "Vector Data",
            "coverageStore": "Raster Data",
        }).get(self.storeType, "Data")

    @property
    def service_type(self):
        if self.storeType == 'coverageStore':
            return "WCS"
        if self.storeType == 'dataStore':
            return "WFS"

    def get_absolute_url(self):
        return reverse('layer_detail', args=(self.typename,))

    def attribute_config(self):
        #Get custom attribute sort order and labels if any
            cfg = {}
            visible_attributes =  self.attribute_set.visible()
            if (visible_attributes.count() > 0):
                cfg["getFeatureInfo"] = {
                    "fields":  [l.attribute for l in visible_attributes],
                    "propertyNames":   dict([(l.attribute,l.attribute_label) for l in visible_attributes])
                }
            return cfg

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
        except ContactRole.DoesNotExist:
            the_ma = None
        return the_ma

    metadata_author = property(_get_metadata_author, _set_metadata_author)

    def keyword_list(self):
        return [kw.name for kw in self.keywords.all()]

    def tiles_url(self):
        return self.link_set.get(name='Tiles').url
        
    def maps(self):
        from geonode.maps.models import MapLayer
        return  MapLayer.objects.filter(name=self.typename)
        

class AttributeManager(models.Manager):
    """Helper class to access filtered attributes
    """

    def visible(self):
       return self.get_query_set().filter(visible=True).order_by('display_order')


class Attribute(models.Model):
    """
        Auxiliary model for storing layer attributes.

       This helps reduce the need for runtime lookups
       to GeoServer, and lets users customize attribute titles,
       sort order, and visibility.
    """
    layer = models.ForeignKey(Layer, blank=False, null=False, unique=False, related_name='attribute_set')
    attribute = models.CharField(_('attribute name'), help_text=_('name of attribute as stored in shapefile/spatial database'), max_length=255, blank=False, null=True, unique=False)
    attribute_label = models.CharField(_('attribute label'), help_text=_('title of attribute as displayed in GeoNode'), max_length=255, blank=False, null=True, unique=False)
    attribute_type = models.CharField(_('attribute type'), help_text=_('the data type of the attribute (integer, string, geometry, etc)'), max_length=50, blank=False, null=False, default='xsd:string', unique=False)
    visible = models.BooleanField(_('visible?'), help_text=_('specifies if the attribute should be displayed in identify results'), default=True)
    display_order = models.IntegerField(_('display order'), help_text=_('specifies the order in which attribute should be displayed in identify results'), default=1)
    objects = AttributeManager()

    def __str__(self):
        return "%s" % self.attribute_label if self.attribute_label else self.attribute

class ContactRole(models.Model):
    """
    ContactRole is an intermediate model to bind Profiles as Contacts to Layers and apply roles.
    """
    contact = models.ForeignKey(Profile)
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

       There are four types of links:
        * original: For uploaded files (Shapefiles or GeoTIFFs)
        * data: For WFS and WCS links that allow access to raw data
        * image: For WMS and TMS links
        * metadata: For CSW links
    """
    layer = models.ForeignKey(Layer)
    extension = models.CharField(max_length=255, help_text=_('For example "kml"'))
    link_type = models.CharField(max_length=255, choices = [(x, x) for x in LINK_TYPES])
    name = models.CharField(max_length=255, help_text=_('For example "View in Google Earth"'))
    mime = models.CharField(max_length=255, help_text=_('For example "text/xml"'))
    url = models.TextField(unique=True, max_length=1000)

    objects = LinkManager()


def geoserver_pre_delete(instance, sender, **kwargs):
    """Removes the layer from GeoServer
    """
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(content_type = ct, object_id = instance.id).delete()
    cascading_delete(Layer.objects.gs_catalog, instance.typename)


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

def post_delete_layer(instance, sender, **kwargs):
    """Removed the layer from any associated map, if any.
    """
    from geonode.maps.models import MapLayer
    logger.debug("Going to delete associated maplayers for [%s]", instance.typename)
    MapLayer.objects.filter(name=instance.typename).delete()

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
    except (EnvironmentError, FailedRequestError) as e:
        gs_resource = None
        msg = ('Could not connect to geoserver at "%s"'
               'to save information for layer "%s"' % (
                settings.GEOSERVER_BASE_URL, instance.name)
              )
        logger.warn(msg, e)
        # If geoserver is not online, there is no need to continue
        return

    # If there is no resource returned it could mean one of two things:
    # a) There is a syncronization problem in geoserver
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
    gs_catalog.save(gs_resource)

    gs_layer = gs_catalog.get_layer(instance.name)

    if instance.poc and instance.poc.user:
        gs_layer.attribution = str(instance.poc.user)
        profile = Profile.objects.get(user=instance.poc.user)
        gs_layer.attribution_link = settings.SITEURL[:-1] + profile.get_absolute_url()
        gs_catalog.save(gs_layer)

    """Get information from geoserver.

       The attributes retrieved include:

       * Bounding Box
       * SRID
       * Download links (WMS, WCS or WFS and KML)
       * Styles (SLD)
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
    except (FailedRequestError, EnvironmentError) as e:
        msg = ('Could not connect to geoserver at "%s"'
               'to save information for layer "%s"' % (
                settings.GEOSERVER_BASE_URL, instance.name)
              )
        logger.warn(msg, e)
        # If geoserver is not online, there is no need to continue
        return

    # If there is no resource returned it could mean one of two things:
    # a) There is a syncronization problem in geoserver
    # b) The unit tests are running and another geoserver is running in the
    # background.
    # For both cases it is sensible to stop processing the layer
    if gs_resource is None:
        logger.warn('Could not get geoserver resource for %s' % instance)
        return

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

    tile_url = ('%sgwc/service/gmaps?' % settings.GEOSERVER_BASE_URL +
                'layers=%s' % instance.typename +
                '&zoom={z}&x={x}&y={y}' +
                '&format=image/png8'
                )

    instance.link_set.get_or_create(url=tile_url,
                       defaults=dict(
                        extension='tiles',
                        name=_("Tiles"),
                        mime='text/png',
                        link_type='image',
                        )
                       )

    #remove links that belong to and old address

    for link in instance.link_set.all():
        if not urlparse(settings.SITEURL).hostname == urlparse(link.url).hostname and not \
                    urlparse(settings.GEOSERVER_BASE_URL).hostname == urlparse(link.url).hostname:

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

def save_style(gs_style):
    style, created = Style.objects.get_or_create(name = gs_style.sld_name)
    style.sld_title = gs_style.sld_title
    style.sld_body = gs_style.sld_body
    style.sld_url = gs_style.body_href()
    style.save()
    return style

def set_attributes(layer):
    """
    Retrieve layer attribute names & types from Geoserver,
    then store in GeoNode database using Attribute model
    """

    #Appending authorizations seems necessary to avoid 'layer not found' from GeoServer
    http = httplib2.Http()
    http.add_credentials(_user, _password)
    _netloc = urlparse(settings.GEOSERVER_BASE_URL).netloc
    http.authorizations.append(
        httplib2.BasicAuthentication(
            (_user, _password),
            _netloc,
            settings.GEOSERVER_BASE_URL,
                {},
            None,
            None,
            http
        )
    )

    attribute_map = []
    if layer.storeType == "dataStore":
        dft_url = settings.GEOSERVER_BASE_URL + "wfs?" + urllib.urlencode({
            "service": "wfs",
            "version": "1.0.0",
            "request": "DescribeFeatureType",
            "typename": layer.typename,
            })
        try:
            body = http.request(dft_url)[1]
            doc = etree.fromstring(body)
            path = ".//{xsd}extension/{xsd}sequence/{xsd}element".format(xsd="{http://www.w3.org/2001/XMLSchema}")
            attribute_map = [[n.attrib["name"],n.attrib["type"]] for n in doc.findall(path)]
        except Exception:
            attribute_map = []
    elif layer.storeType == "coverageStore":
        dc_url = settings.GEOSERVER_BASE_URL + "wcs?" + urllib.urlencode({
            "service": "wcs",
            "version": "1.1.0",
            "request": "DescribeCoverage",
            "identifiers": layer.typename
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
        if not lafound:
            logger.debug("Going to delete [%s] for [%s]", la.attribute, layer.name)
            la.delete()

    # Add new layer attributes if they don't already exist
    if attribute_map is not None:
        iter = len(Attribute.objects.filter(layer=layer)) + 1
        for field, ftype in attribute_map:
            if field is not None:
                la, created = Attribute.objects.get_or_create(layer=layer, attribute=field, attribute_type=ftype)
                if created:
                    la.attribute_label = field.title()
                    la.visible = ftype.find("gml:") != 0
                    la.display_order = iter
                    la.save()
                    iter += 1
                    logger.debug("Created [%s] attribute for [%s]", field, layer.name)
    else:
        logger.debug("No attributes found")

signals.pre_save.connect(pre_save_layer, sender=Layer)
signals.pre_save.connect(geoserver_pre_save, sender=Layer)
signals.pre_delete.connect(geoserver_pre_delete, sender=Layer)
signals.post_save.connect(geoserver_post_save, sender=Layer)
signals.post_delete.connect(post_delete_layer, sender=Layer)

