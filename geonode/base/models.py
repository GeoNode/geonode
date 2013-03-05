from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings

from geonode.base.enumerations import COUNTRIES, ALL_LANGUAGES, \
    HIERARCHY_LEVELS, UPDATE_FREQUENCIES, CONSTRAINT_OPTIONS, \
    SPATIAL_REPRESENTATION_TYPES, \
    DEFAULT_SUPPLEMENTAL_INFORMATION, LINK_TYPES
from geonode.utils import bbox_to_wkt
from geonode.people.models import Profile, Role
from geonode.security.models import PermissionLevelMixin

from taggit.managers import TaggableManager

def get_default_category():
    if settings.DEFAULT_TOPICCATEGORY:
        try:
            return TopicCategory.objects.get(slug=settings.DEFAULT_TOPICCATEGORY)
        except TopicCategory.DoesNotExist:
            raise TopicCategory.DoesNotExist('The default TopicCategory indicated in settings is not found.')
    else:
        return TopicCategory.objects.all()[0]

class ContactRole(models.Model):
    """
    ContactRole is an intermediate abstract model to bind Profiles as Contacts to Layers and apply roles.
    """
    resource = models.ForeignKey('ResourceBase', null=True)
    contact = models.ForeignKey(Profile)
    role = models.ForeignKey(Role)

    def clean(self):
        """
        Make sure there is only one poc and author per resource
        """
        if (self.role == self.resource.poc_role) or (self.role == self.resource.metadata_author_role):
            contacts = self.resource.contacts.filter(contactrole__role=self.role)
            if contacts.count() == 1:
                # only allow this if we are updating the same contact
                if self.contact != contacts.get():
                    raise ValidationError('There can be only one %s for a given resource' % self.role)
        if self.contact.user is None:
            # verify that any unbound contact is only associated to one resource
            bounds = ContactRole.objects.filter(contact=self.contact).count()
            if bounds > 1:
                raise ValidationError('There can be one and only one resource linked to an unbound contact' % self.role)
            elif bounds == 1:
                # verify that if there was one already, it corresponds to this instace
                if ContactRole.objects.filter(contact=self.contact).get().id != self.id:
                    raise ValidationError('There can be one and only one resource linked to an unbound contact' % self.role)

    class Meta:
        unique_together = (("contact", "resource", "role"),)

class TopicCategory(models.Model):

    name = models.CharField(max_length=50)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    def __unicode__(self):
        return u"{0}".format(self.name)

    @property
    def counts(self):
        counts = {
            'layers': 0,
            'maps': 0,
            'documents': 0
        }
        for resource in self.resourcebase_set.all():
            try:
                resource.layer
                counts['layers'] += 1
            except ObjectDoesNotExist:
                pass
            try:
                resource.map
                counts['maps'] += 1
            except ObjectDoesNotExist:
                pass
            try: 
                resource.document
                counts['documents'] += 1
            except ObjectDoesNotExist:
                pass
        return counts

    class Meta:
        ordering = ("name",)
        verbose_name_plural = 'Topic Categories'

class ResourceBaseManager(models.Manager):

    def __init__(self):
        models.Manager.__init__(self)

    def admin_contact(self):
        # this assumes there is at least one superuser
        superusers = User.objects.filter(is_superuser=True).order_by('id')
        if superusers.count() == 0:
            raise RuntimeError('GeoNode needs at least one admin/superuser set')

        contact = Profile.objects.get_or_create(user=superusers[0],
                                                defaults={"name": "Geonode Admin"})[0]
        return contact

class ResourceBase(models.Model, PermissionLevelMixin):
    """
    Base Resource Object loosely based on ISO 19115:2003
    """

    VALID_DATE_TYPES = [(x.lower(), _(x)) for x in ['Creation', 'Publication', 'Revision']]

    # internal fields
    uuid = models.CharField(max_length=36)
    owner = models.ForeignKey(User, blank=True, null=True)

    contacts = models.ManyToManyField(Profile, through='ContactRole')

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

    def __unicode__(self):
        return self.title

    @property
    def bbox(self):
        return [self.bbox_x0, self.bbox_x1, self.bbox_y0, self.bbox_y1, self.srid]

    @property
    def bbox_string(self):
        return ",".join([str(self.bbox_x0), str(self.bbox_x1), str(self.bbox_y0), str(self.bbox_y1)])

    @property
    def geographic_bounding_box(self):
        return bbox_to_wkt(self.bbox_x0, self.bbox_x1, self.bbox_y0, self.bbox_y1, srid=self.srid )

    def get_extent(self):
        """Generate minx/miny/maxx/maxy of map extent"""

        return self.bbox

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

    def set_latlon_bounds(self,box):
        """
        Set the four bounds in lat lon projection
        """
        self.bbox_x0 = box[0]
        self.bbox_x1 = box[1]
        self.bbox_y0 = box[2]
        self.bbox_y1 = box[3]

    def _set_poc(self, poc):
        # reset any poc asignation to this resource
        ContactRole.objects.filter(role=self.poc_role, resource=self).delete()
        #create the new assignation
        ContactRole.objects.create(role=self.poc_role, resource=self, contact=poc)

    def _get_poc(self):
        try:
            the_poc = ContactRole.objects.get(role=self.poc_role, resource=self).contact
        except ContactRole.DoesNotExist:
            the_poc = None
        return the_poc

    poc = property(_get_poc, _set_poc)

    def _set_metadata_author(self, metadata_author):
        # reset any metadata_author asignation to this resource
        ContactRole.objects.filter(role=self.metadata_author_role, resource=self).delete()
        #create the new assignation
        ContactRole.objects.create(role=self.metadata_author_role,
                                                  resource=self, contact=metadata_author)

    def _get_metadata_author(self):
        try:
            the_ma = ContactRole.objects.get(role=self.metadata_author_role, resource=self).contact
        except ContactRole.DoesNotExist:
            the_ma = None
        return the_ma

    metadata_author = property(_get_metadata_author, _set_metadata_author)

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
    """Auxiliary model for storying links for resources.

       This helps avoiding the need for runtime lookups
       to the OWS server or the CSW Catalogue.

       There are four types of links:
        * original: For uploaded files (Shapefiles or GeoTIFFs)
        * data: For WFS and WCS links that allow access to raw data
        * image: For WMS and TMS links
        * metadata: For CSW links
    """
    resource = models.ForeignKey(ResourceBase)
    extension = models.CharField(max_length=255, help_text=_('For example "kml"'))
    link_type = models.CharField(max_length=255, choices = [(x, x) for x in LINK_TYPES])
    name = models.CharField(max_length=255, help_text=_('For example "View in Google Earth"'))
    mime = models.CharField(max_length=255, help_text=_('For example "text/xml"'))
    url = models.TextField(unique=True, max_length=1000)

    objects = LinkManager()