from datetime import datetime
import os
import hashlib

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.staticfiles.templatetags import staticfiles

from geonode.base.enumerations import ALL_LANGUAGES, \
    HIERARCHY_LEVELS, UPDATE_FREQUENCIES, \
    DEFAULT_SUPPLEMENTAL_INFORMATION, LINK_TYPES
from geonode.utils import bbox_to_wkt
from geonode.people.models import Profile, Role
from geonode.security.models import PermissionLevelMixin

from taggit.managers import TaggableManager

def get_default_category():
    if settings.DEFAULT_TOPICCATEGORY:
        try:
            return TopicCategory.objects.get(identifier=settings.DEFAULT_TOPICCATEGORY)
        except TopicCategory.DoesNotExist:
            raise TopicCategory.DoesNotExist('The default TopicCategory indicated in settings is not found.')
    else:
        return TopicCategory.objects.all()[0]

class ContactRole(models.Model):
    """
    ContactRole is an intermediate abstract model to bind Profiles as Contacts to Layers and apply roles.
    """
    resource = models.ForeignKey('ResourceBase')
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
                # verify that if there was one already, it corresponds to this instance
                if ContactRole.objects.filter(contact=self.contact).get().id != self.id:
                    raise ValidationError('There can be one and only one resource linked to an unbound contact' % self.role)

    class Meta:
        unique_together = (("contact", "resource", "role"),)

class TopicCategory(models.Model):
    """
    Metadata about high-level geographic data thematic classification.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_MD_TopicCategoryCode">
    """
    identifier = models.CharField(max_length=255, default='location')
    description = models.TextField()
    gn_description = models.TextField('GeoNode description', default='', null=True)
    is_choice = models.BooleanField(default=True)

    def __unicode__(self):
        return u"{0}".format(self.gn_description)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Metadata Topic Categories'
        
class SpatialRepresentationType(models.Model):
    """
    Metadata information about the spatial representation type.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_SpatialRepresentationTypeCode">
    """
    identifier = models.CharField(max_length=255, editable=False)
    description = models.CharField(max_length=255, editable=False)
    gn_description = models.CharField('GeoNode description', max_length=255)
    is_choice = models.BooleanField(default=True)

    def __unicode__(self):
        return self.gn_description

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Metadata Spatial Representation Types'
        
class Region(models.Model):

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ("name",)
        verbose_name_plural = 'Metadata Regions'
        
class RestrictionCodeType(models.Model):
    """
    Metadata information about the spatial representation type.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_RestrictionCode">
    """
    identifier = models.CharField(max_length=255, editable=False)
    description = models.TextField(max_length=255, editable=False)
    gn_description = models.TextField('GeoNode description', max_length=255)
    is_choice = models.BooleanField(default=True)

    def __unicode__(self):
        return self.gn_description

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Metadata Restriction Code Types'

class Thumbnail(models.Model):

    thumb_file = models.FileField(upload_to='thumbs')
    thumb_spec = models.TextField(null=True, blank=True)
    version = models.PositiveSmallIntegerField(null=True, default=0)

    def save_thumb(self, image, id):
        """image must be png data in a string for now"""
        self._delete_thumb()
        md5 = hashlib.md5()
        md5.update(id + str(self.version))
        self.version = self.version + 1
        self.thumb_file.save(md5.hexdigest() + ".png", ContentFile(image))

    def _delete_thumb(self):
        try:
            self.thumb_file.delete()
        except OSError:
            pass

    def delete(self):
        self._delete_thumb()
        super(Thumbnail,self).delete()


class ThumbnailMixin(object):
    """
    Add Thumbnail management behavior. The model must declared a field
    named thumbnail.
    """

    def save_thumbnail(self, spec, save=True):
        """
        Generic support for saving. `render` implementation must exist
        and return image as bytes of a png image (for now)
        """
        render = getattr(self, '_render_thumbnail', None)
        if render is None:
            raise Exception('Must have _render_thumbnail(spec) function')
        image = render(spec)

        if not image:
            return

        #Clean any orphan Thumbnail before
        Thumbnail.objects.filter(resourcebase__id=None).delete()
        
        self.thumbnail, created = Thumbnail.objects.get_or_create(resourcebase__id=self.id)
        path = self._thumbnail_path()
        self.thumbnail.thumb_spec = spec
        self.thumbnail.save_thumb(image, path)
        # have to save the thumb ref if new but also trigger XML regeneration
        if save:
            self.save()

    def _thumbnail_path(self):
        return '%s-%s' % (self._meta.object_name, self.pk)

    def _get_default_thumbnail(self):
        return getattr(self, "_missing_thumbnail", staticfiles.static(settings.MISSING_THUMBNAIL))

    def get_thumbnail_url(self):
        thumb = self.thumbnail
        return thumb == None and self._get_default_thumbnail() or thumb.thumb_file.url
 
    def has_thumbnail(self):
        '''Determine if the thumbnail object exists and an image exists'''
        thumb = self.thumbnail
        return os.path.exists(self._thumbnail_path()) if thumb else False


class ResourceBaseManager(models.Manager):
    def admin_contact(self):
        # this assumes there is at least one superuser
        superusers = User.objects.filter(is_superuser=True).order_by('id')
        if superusers.count() == 0:
            raise RuntimeError('GeoNode needs at least one admin/superuser set')

        contact = Profile.objects.get_or_create(user=superusers[0],
                                                defaults={"name": "Geonode Admin"})[0]
        return contact


class License(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    license_text = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class ResourceBase(models.Model, PermissionLevelMixin, ThumbnailMixin):
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
    regions = models.ManyToManyField(Region, verbose_name=_('keywords region'), help_text=_('keyword identifies a location'), blank=True)
    restriction_code_type = models.ForeignKey(RestrictionCodeType, verbose_name=_('restrictions'), help_text=_('limitation(s) placed upon the access or use of the data.'), null=True, blank=True, limit_choices_to=Q(is_choice=True))
    constraints_other = models.TextField(_('restrictions other'), blank=True, null=True, help_text=_('other restrictions and legal prerequisites for accessing and using the resource or metadata'))

    license = models.ForeignKey(License, null=True, blank=True)

    # Section 4
    language = models.CharField(_('language'), max_length=3, choices=ALL_LANGUAGES, default='eng', help_text=_('language used within the dataset'))
    category = models.ForeignKey(TopicCategory, help_text=_('high-level geographic data thematic classification to assist in the grouping and search of available geographic data sets.'), 
        null=True, blank=True, limit_choices_to=Q(is_choice=True))
    spatial_representation_type = models.ForeignKey(SpatialRepresentationType, help_text=_('method used to represent geographic information in the dataset.'), null=True, blank=True, limit_choices_to=Q(is_choice=True))

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
    csw_anytext = models.TextField(_('CSW anytext'), null=True, blank=True)
    csw_wkt_geometry = models.TextField(_('CSW WKT geometry'), null=False, default='POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))')

    # metadata XML specific fields
    metadata_uploaded = models.BooleanField(default=False)
    metadata_xml = models.TextField(null=True, default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>', blank=True)

    thumbnail = models.ForeignKey(Thumbnail, null=True, blank=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.title
        
    @property
    def geonode_type(self):
        gn_type = ''
        try:
            self.layer
            gn_type = 'layer'
        except:
            pass
        try:
            self.map
            gn_type = 'map'
        except:
            pass
        try:
            self.document
            gn_type = 'document'
        except:
            pass
        return gn_type

    @property
    def bbox(self):
        return [self.bbox_x0, self.bbox_y0, self.bbox_x1, self.bbox_y1, self.srid]

    @property
    def bbox_string(self):
        return ",".join([str(self.bbox_x0), str(self.bbox_y0), str(self.bbox_x1), str(self.bbox_y1)])

    @property
    def geographic_bounding_box(self):
        return bbox_to_wkt(self.bbox_x0, self.bbox_x1, self.bbox_y0, self.bbox_y1, srid=self.srid )

    def get_extent(self):
        """Generate minx/miny/maxx/maxy of map extent"""

        return self.bbox

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

    def spatial_representation_type_string(self):
        if hasattr(self.spatial_representation_type, 'identifier'):
            return self.spatial_representation_type.identifier
        else:
            if hasattr(self, 'storeType'): 
                if self.storeType == 'coverageStore':
                    return 'grid'
                return 'vector'
            else:
                return None

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

    def download_links(self):
        """assemble download links for pycsw"""
        links = []
        for url in self.link_set.all():
            if url.link_type == 'metadata':  # avoid recursion
                continue
            if url.link_type == 'html':
                links.append((self.title, 'Web address (URL)', 'WWW:LINK-1.0-http--link', url.url))
            elif url.link_type in ('OGC:WMS', 'OGC:WFS', 'OGC:WCS'):
                links.append((self.title, description, url.link_type, url.url))
            else:
                description = '%s (%s Format)' % (self.title, url.name)
                links.append((self.title, description, 'WWW:DOWNLOAD-1.0-http--download', url.url))
        return links
    
    def maintenance_frequency_title(self):
        return [v for i, v in enumerate(UPDATE_FREQUENCIES) if v[0] == self.maintenance_frequency][0][1].title()
        
    def language_title(self):
        return [v for i, v in enumerate(ALL_LANGUAGES) if v[0] == self.language][0][1].title()
    
    def _set_poc(self, poc):
        # reset any poc assignation to this resource
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
        # reset any metadata_author assignation to this resource
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

    objects = ResourceBaseManager()

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
    """Auxiliary model for storing links for resources.

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
    url = models.TextField(max_length=1000)

    objects = LinkManager()

def resourcebase_post_save(instance, sender, **kwargs):
    """
    Since django signals are not propagated from child to parent classes we need to call this 
    from the children.
    TODO: once the django will support signal propagation we need to attach a single signal here
    """
    resourcebase = instance.resourcebase_ptr
    if resourcebase.owner:
        user = resourcebase.owner
    else:
        user = ResourceBase.objects.admin_contact().user
        
    if resourcebase.poc is None:
        pc, __ = Profile.objects.get_or_create(user=user,
                                           defaults={"name": user.username}
                                           )
        resourcebase.poc = pc
    if resourcebase.metadata_author is None:  
        ac, __ = Profile.objects.get_or_create(user=user,
                                           defaults={"name": user.username}
                                           )
        resourcebase.metadata_author = ac

def resourcebase_post_delete(instance, sender, **kwargs):
    """
    Since django signals are not propagated from child to parent classes we need to call this 
    from the children.
    TODO: once the django will support signal propagation we need to attach a single signal here
    """
    if instance.thumbnail:
        instance.thumbnail.delete()
        
    
