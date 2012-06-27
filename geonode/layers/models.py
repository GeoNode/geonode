# -*- coding: utf-8 -*-
import httplib2
import urllib
import logging
import sys
import uuid

from datetime import datetime
from lxml import etree

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from geonode import GeoNodeException
from geonode.utils import _wms, _user, _password, get_wms, bbox_to_wkt
from geonode.csw import get_record, create_record, remove_record
from geonode.gs_helpers import cascading_delete
from geonode.people.models import Contact, Role 
from geonode.security.models import PermissionLevelMixin
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.layers.enumerations import COUNTRIES, ALL_LANGUAGES, \
    UPDATE_FREQUENCIES, CONSTRAINT_OPTIONS, SPATIAL_REPRESENTATION_TYPES, \
    TOPIC_CATEGORIES, DEFAULT_SUPPLEMENTAL_INFORMATION

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

    def default_poc(self):
        return self.admin_contact()

    def default_metadata_author(self):
        return self.admin_contact()

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
    keywords = TaggableManager(_('keywords'), help_text=_("A space or comma-separated list of keywords"))
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
    geographic_bounding_box = models.TextField(_('geographic bounding box'))
    supplemental_information = models.TextField(_('supplemental information'), default=DEFAULT_SUPPLEMENTAL_INFORMATION)

    # Section 6
    distribution_url = models.TextField(_('distribution URL'), blank=True, null=True)
    distribution_description = models.TextField(_('distribution description'), blank=True, null=True)

    # Section 8
    data_quality_statement = models.TextField(_('data quality statement'), blank=True, null=True)

    # Section 9
    # see metadata_author property definition below

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

        bbox = self.resource.latlon_bbox
        bbox_string = ",".join([bbox[0], bbox[2], bbox[1], bbox[3]])

        return settings.GEOSERVER_BASE_URL + "wms?" + urllib.urlencode({
            'service': 'WMS',
            'version': '1.1.1',
            'request': 'GetMap',
            'layers': self.typename,
            'format': 'image/png',
            'height': height,
            'width': width,
            'srs': 'EPSG:4326',
            'bbox': bbox_string})

    def download_links(self):
        """Returns a list of (mimetype, URL) tuples for downloads of this data
        in various formats."""
 
        bbox = self.resource.latlon_bbox

        dx = float(bbox[1]) - float(bbox[0])
        dy = float(bbox[3]) - float(bbox[2])

        dataAspect = 1 if dy == 0 else dx / dy

        height = 550
        width = int(height * dataAspect)

        # bbox: this.adjustBounds(widthAdjust, heightAdjust, values.llbbox).toString(),

        srs = 'EPSG:4326' # bbox[4] might be None
        bbox_string = ",".join([bbox[0], bbox[2], bbox[1], bbox[3]])

        links = []        

        if self.resource.resource_type == "featureType":
            def wfs_link(mime, extra_params):
                params = {
                    'service': 'WFS',
                    'version': '1.0.0',
                    'request': 'GetFeature',
                    'typename': self.typename,
                    'outputFormat': mime
                }
                params.update(extra_params)
                return settings.GEOSERVER_BASE_URL + "wfs?" + urllib.urlencode(params)

            types = [
                ("zip", _("Zipped Shapefile"), "SHAPE-ZIP", {'format_options': 'charset:UTF-8'}),
                ("gml", _("GML 2.0"), "gml2", {}),
                ("gml", _("GML 3.1.1"), "text/xml; subtype=gml/3.1.1", {}),
                ("csv", _("CSV"), "csv", {}),
                ("excel", _("Excel"), "excel", {}),
                ("json", _("GeoJSON"), "json", {})
            ]
            links.extend((ext, name, wfs_link(mime, extra_params)) for ext, name, mime, extra_params in types)
        elif self.resource.resource_type == "coverage":
            try:
                client = httplib2.Http()
                description_url = settings.GEOSERVER_BASE_URL + "wcs?" + urllib.urlencode({
                        "service": "WCS",
                        "version": "1.0.0",
                        "request": "DescribeCoverage",
                        "coverage": self.typename
                    })
                content = client.request(description_url)[1]
                doc = etree.fromstring(content)
                extent = doc.find(".//%(gml)slimits/%(gml)sGridEnvelope" % {"gml": "{http://www.opengis.net/gml}"}) 
                low = extent.find("{http://www.opengis.net/gml}low").text.split()
                high = extent.find("{http://www.opengis.net/gml}high").text.split()
                w, h = [int(h) - int(l) for (h, l) in zip(high, low)]

                def wcs_link(mime):
                    return settings.GEOSERVER_BASE_URL + "wcs?" + urllib.urlencode({
                        "service": "WCS",
                        "version": "1.0.0",
                        "request": "GetCoverage",
                        "CRS": "EPSG:4326",
                        "height": h,
                        "width": w,
                        "coverage": self.typename,
                        "bbox": bbox_string,
                        "format": mime
                    })

                types = [("tiff", "GeoTIFF", "geotiff")]
                links.extend([(ext, name, wcs_link(mime)) for (ext, name, mime) in types])
            except Exception:
                # if something is wrong with WCS we probably don't want to link
                # to it anyway
                # TODO: This is a bad idea to eat errors like this.
                pass 

        def wms_link(mime):
            return settings.GEOSERVER_BASE_URL + "wms?" + urllib.urlencode({
                'service': 'WMS',
                'request': 'GetMap',
                'layers': self.typename,
                'format': mime,
                'height': height,
                'width': width,
                'srs': srs,
                'bbox': bbox_string
            })

        types = [
            ("jpg", _("JPEG"), "image/jpeg"),
            ("pdf", _("PDF"), "application/pdf"),
            ("png", _("PNG"), "image/png")
        ]

        links.extend((ext, name, wms_link(mime)) for ext, name, mime in types)

        kml_reflector_link_download = settings.GEOSERVER_BASE_URL + "wms/kml?" + urllib.urlencode({
            'layers': self.typename,
            'mode': "download"
        })

        kml_reflector_link_view = settings.GEOSERVER_BASE_URL + "wms/kml?" + urllib.urlencode({
            'layers': self.typename,
            'mode': "refresh"
        })

        links.append(("KML", _("KML"), kml_reflector_link_download))
        links.append(("KML", _("View in Google Earth"), kml_reflector_link_view))

        return links

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
        
        # Check the layer is in GeoServer's REST API
        # It would be nice if we could ask for the definition of a layer by name
        # rather than searching for it
        #api_url = "%sdata/search/api/?q=%s" % (settings.SITEURL, self.name.replace('_', '%20'))
        #response, body = http.request(api_url)
        #api_json = json.loads(body)
        #api_layer = None
        #for row in api_json['rows']:
        #    if(row['name'] == self.typename):
        #        api_layer = row
        #if(api_layer == None):
        #    msg = "API Record missing for layer [%s]" % self.typename
        #    raise GeoNodeException(msg)
 
        # Check the layer is in the GeoNetwork catalog and points back to get_absolute_url

        # Check the layer is in the catalogue and points back to get_absolute_url
        catalogue_layer = get_record(self.uuid)

        if hasattr(catalogue_layer, 'distribution') and hasattr(catalogue_layer.distribution, 'online'):
            for link in catalogue_layer.distribution.online:
                if link.protocol == 'WWW:LINK-1.0-http--link':
                    if(link.url != self.get_absolute_url()):
                        msg = "Catalogue Layer URL does not match layer URL for layer [%s]" % self.typename
        else:        
            msg = "Catalogue Layer URL not found layer [%s]" % self.typename


        # if(csw_layer.uri != self.get_absolute_url()):
        #     msg = "CSW Layer URL does not match layer URL for layer [%s]" % self.typename

        # Visit get_absolute_url and make sure it does not give a 404
        #logger.info(self.get_absolute_url())
        #response, body = http.request(self.get_absolute_url())
        #if(int(response['status']) != 200):
        #    msg = "Layer Info page for layer [%s] is %d" % (self.typename, int(response['status']))
        #    raise GeoNodeException(msg)

        #FIXME: Add more checks, for example making sure the title, keywords and description
        # are the same in every database.

    #def maps(self):
    #    """Return a list of all the maps that use this layer"""
    #    local_wms = "%swms" % settings.GEOSERVER_BASE_URL
    #    return set([layer.map for layer in MapLayer.objects.filter(ows_url=local_wms, name=self.typename).select_related()])

    def metadata(self):
        if (_wms is None) or (self.typename not in _wms.contents):
            get_wms()
            # wms_url = "%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL
            # netloc = urlparse(wms_url).netloc
            # http = httplib2.Http()
            # http.add_credentials(_user, _password)
            # http.authorizations.append(
            #     httplib2.BasicAuthentication(
            #         (_user, _password), 
            #         netloc,
            #         wms_url,
            #         {},
            #         None,
            #         None, 
            #         http
            #     )
            # )
            # response, body = http.request(wms_url)
            # _wms = WebMapService(wms_url, xml=body)
        return _wms[self.typename]

    def metadata_record(self):
        return get_record(self.uuid)

    @property
    def attribute_names(self):
        if self.resource.resource_type == "featureType":
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
        elif self.resource.resource_type == "coverage":
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
            except AttributeError:
                # Geoserver is not running
                raise RuntimeError("Geoserver cannot be accessed, are you sure it is running in: %s" %
                                    (settings.GEOSERVER_BASE_URL))
            store = cat.get_store(self.store, ws)
            self._resource_cache = cat.get_resource(self.name, store)
        return self._resource_cache

    def _get_metadata_links(self):
        return self.resource.metadata_links

    def _set_metadata_links(self, md_links):
        self.resource.metadata_links = md_links

    metadata_links = property(_get_metadata_links, _set_metadata_links)

    @property
    def full_metadata_links(self):
        """Returns complete list of dicts of possible Catalogue metadata URLs
           NOTE: we are NOT using the above properties because this will
           break the OGC W*S Capabilities rules
        """
        record = get_record(self.uuid)
        metadata_links = record.links['metadata']
        return metadata_links

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

    def save_to_geoserver(self):
        if self.resource is None:
            return
        if hasattr(self, "_resource_cache"):
            self.resource.title = self.title
            self.resource.abstract = self.abstract
            self.resource.name= self.name
            self.resource.keywords = self.keyword_list()

            # Get metadata link from csw catalog
            record = get_record(self.uuid)
            self.resource.metadata_links = record.links['metadata']
 
            Layer.objects.gs_catalog.save(self._resource_cache)
        if self.poc and self.poc.user:
            self.publishing.attribution = str(self.poc.user)
            profile = Contact.objects.get(user=self.poc.user)
            self.publishing.attribution_link = settings.SITEURL[:-1] + profile.get_absolute_url()
            Layer.objects.gs_catalog.save(self.publishing)

    def  _populate_from_gs(self):
        gs_resource = Layer.objects.gs_catalog.get_resource(self.name)
        if gs_resource is None:
            return
        srs = gs_resource.projection
        if self.geographic_bounding_box is '' or self.geographic_bounding_box is None:
            self.set_bbox(gs_resource.native_bbox, srs=srs)

    def _autopopulate(self):
        if self.poc is None:
            self.poc = Layer.objects.default_poc()
        if self.metadata_author is None:
            self.metadata_author = Layer.objects.default_metadata_author()
        if self.abstract == '' or self.abstract is None:
            self.abstract = 'No abstract provided'
        if self.title == '' or self.title is None:
            self.title = self.name

    def _populate_from_catalogue(self):
        meta = self.metadata_record()
        if meta is None:
            return
        kw_list = reduce(
                lambda x, y: x + y["keywords"],
                meta.identification.keywords,
                [])
        kw_list = [l for l in kw_list if l is not None]
        self.keywords.add(*kw_list)
        if hasattr(meta.distribution, 'online'):
            onlineresources = [r for r in meta.distribution.online if r.protocol == "WWW:LINK-1.0-http--link"]
            if len(onlineresources) == 1:
                res = onlineresources[0]
                self.distribution_url = res.url
                self.distribution_description = res.description

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def set_bbox(self, box, srs=None):
        """
        Sets a bounding box based on the gsconfig native_box param.
        """
        if srs:
            srid = srs
        else:
            srid = box[4]
        self.geographic_bounding_box = bbox_to_wkt(box[0], box[1], box[2], box[3], srid=srid )

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
    layer = models.ForeignKey(Layer)
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


def delete_layer(instance, sender, **kwargs): 
    """
    Removes the layer from GeoServer and Catalogue
    """
    instance.delete_from_geoserver()
    remove_record(instance)

def post_save_layer(instance, sender, **kwargs):
    instance._autopopulate()

    # If this object was saved via fixtures,
    # do not do post processing.
    if kwargs.get('raw', False):
        return

    instance.save_to_geoserver()

    if kwargs['created']:
        instance._populate_from_gs()

    create_record(instance)

    if kwargs['created']:
        instance._populate_from_catalogue()
        instance.save(force_update=True)


signals.pre_delete.connect(delete_layer, sender=Layer)
signals.post_save.connect(post_save_layer, sender=Layer)
