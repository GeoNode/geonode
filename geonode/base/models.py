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

import datetime
import math
import os
import re
import logging
import traceback
import uuid
import urllib
import urllib2
import cookielib

from geonode.decorators import on_ogc_backend
from pyproj import transform, Proj
from urlparse import urljoin, urlsplit

from django.db import models
from django.core import serializers
from django.db.models import Q, signals
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.staticfiles.templatetags import staticfiles
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.files.storage import default_storage as storage
from django.core.files.base import ContentFile
from django.contrib.gis.geos import GEOSGeometry
from django.utils.timezone import now

from mptt.models import MPTTModel, TreeForeignKey

from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager
from agon_ratings.models import OverallRating

from geonode import geoserver
from geonode.base.enumerations import ALL_LANGUAGES, \
    HIERARCHY_LEVELS, UPDATE_FREQUENCIES, \
    DEFAULT_SUPPLEMENTAL_INFORMATION, LINK_TYPES
from geonode.utils import bbox_to_wkt
from geonode.utils import forward_mercator
from geonode.security.models import PermissionLevelMixin
from taggit.managers import TaggableManager, _TaggableManager
from taggit.models import TagBase, ItemBase
from treebeard.mp_tree import MP_Node

from geonode.people.enumerations import ROLE_VALUES

from oauthlib.common import generate_token
from oauth2_provider.models import AccessToken, get_application_model

logger = logging.getLogger(__name__)


class ContactRole(models.Model):
    """
    ContactRole is an intermediate model to bind Profiles as Contacts to Resources and apply roles.
    """
    resource = models.ForeignKey('ResourceBase', blank=True, null=True)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL)
    role = models.CharField(
        choices=ROLE_VALUES,
        max_length=255,
        help_text=_(
            'function performed by the responsible '
            'party'))

    def clean(self):
        """
        Make sure there is only one poc and author per resource
        """
        if (self.role == self.resource.poc_role) or (
                self.role == self.resource.metadata_author_role):
            contacts = self.resource.contacts.filter(
                contactrole__role=self.role)
            if contacts.count() == 1:
                # only allow this if we are updating the same contact
                if self.contact != contacts.get():
                    raise ValidationError(
                        'There can be only one %s for a given resource' %
                        self.role)
        if self.contact.user is None:
            # verify that any unbound contact is only associated to one
            # resource
            bounds = ContactRole.objects.filter(contact=self.contact).count()
            if bounds > 1:
                raise ValidationError(
                    'There can be one and only one resource linked to an unbound contact' %
                    self.role)
            elif bounds == 1:
                # verify that if there was one already, it corresponds to this
                # instance
                if ContactRole.objects.filter(
                        contact=self.contact).get().id != self.id:
                    raise ValidationError(
                        'There can be one and only one resource linked to an unbound contact' %
                        self.role)

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
    description = models.TextField(default='')
    gn_description = models.TextField(
        'GeoNode description', default='', null=True)
    is_choice = models.BooleanField(default=True)
    fa_class = models.CharField(max_length=64, default='fa-times')

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


class RegionManager(models.Manager):
    def get_by_natural_key(self, code):
        return self.get(code=code)


class Region(MPTTModel):
    # objects = RegionManager()

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children')

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images
    # and metadata records.
    bbox_x0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_x1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    srid = models.CharField(
        max_length=30,
        blank=False,
        null=False,
        default='EPSG:4326')

    def __unicode__(self):
        return self.name

    @property
    def bbox(self):
        """BBOX is in the format: [x0,x1,y0,y1]."""
        return [
            self.bbox_x0,
            self.bbox_x1,
            self.bbox_y0,
            self.bbox_y1,
            self.srid]

    @property
    def bbox_string(self):
        """BBOX is in the format: [x0,y0,x1,y1]."""
        return ",".join([str(self.bbox_x0), str(self.bbox_y0),
                         str(self.bbox_x1), str(self.bbox_y1)])

    @property
    def geographic_bounding_box(self):
        """BBOX is in the format: [x0,x1,y0,y1]."""
        return bbox_to_wkt(
            self.bbox_x0,
            self.bbox_x1,
            self.bbox_y0,
            self.bbox_y1,
            srid=self.srid)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = 'Metadata Regions'

    class MPTTMeta:
        order_insertion_by = ['name']


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


class Backup(models.Model):
    identifier = models.CharField(max_length=255, editable=False)
    name = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True, blank=True)
    description = models.TextField(null=True, blank=True)
    base_folder = models.CharField(max_length=100)
    location = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("date", )
        verbose_name_plural = 'Backups'


class License(models.Model):
    identifier = models.CharField(max_length=255, editable=False)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    license_text = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    @property
    def name_long(self):
        if self.abbreviation is None or len(self.abbreviation) == 0:
            return self.name
        else:
            return self.name + " (" + self.abbreviation + ")"

    @property
    def description_bullets(self):
        if self.description is None or len(self.description) == 0:
            return ""
        else:
            bullets = []
            lines = self.description.split("\n")
            for line in lines:
                bullets.append("+ " + line)
            return bullets

    class Meta:
        ordering = ("name", )
        verbose_name_plural = 'Licenses'


class HierarchicalKeyword(TagBase, MP_Node):
    node_order_by = ['name']

    @classmethod
    def dump_bulk_tree(cls, parent=None, keep_ids=True):
        """Dumps a tree branch to a python data structure."""
        qset = cls._get_serializable_model().get_tree(parent)
        ret, lnk = [], {}
        for pyobj in qset:
            serobj = serializers.serialize('python', [pyobj])[0]
            # django's serializer stores the attributes in 'fields'
            fields = serobj['fields']
            depth = fields['depth'] or 1
            fields['text'] = fields['name']
            fields['href'] = fields['slug']
            del fields['name']
            del fields['slug']
            del fields['path']
            del fields['numchild']
            del fields['depth']
            if 'id' in fields:
                # this happens immediately after a load_bulk
                del fields['id']

            newobj = {}
            for field in fields:
                newobj[field] = fields[field]
            if keep_ids:
                newobj['id'] = serobj['pk']

            if (not parent and depth == 1) or\
               (parent and depth == parent.depth):
                ret.append(newobj)
            else:
                parentobj = pyobj.get_parent()
                parentser = lnk[parentobj.pk]
                if 'nodes' not in parentser:
                    parentser['nodes'] = []
                parentser['nodes'].append(newobj)
            lnk[pyobj.pk] = newobj
        return ret


class TaggedContentItem(ItemBase):
    content_object = models.ForeignKey('ResourceBase')
    tag = models.ForeignKey('HierarchicalKeyword', related_name='keywords')

    # see https://github.com/alex/django-taggit/issues/101
    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return cls.tag_model().objects.filter(**{
                '%s__content_object' % cls.tag_relname(): instance
            })
        return cls.tag_model().objects.filter(**{
            '%s__content_object__isnull' % cls.tag_relname(): False
        }).distinct()


class _HierarchicalTagManager(_TaggableManager):

    def add(self, *tags):
        str_tags = set([
            t
            for t in tags
            if not isinstance(t, self.through.tag_model())
        ])
        tag_objs = set(tags) - str_tags
        # If str_tags has 0 elements Django actually optimizes that to not do a
        # query.  Malcolm is very smart.
        existing = self.through.tag_model().objects.filter(
            name__in=str_tags
        )
        tag_objs.update(existing)
        for new_tag in str_tags - set(t.name for t in existing):
            if new_tag:
                tag_objs.add(HierarchicalKeyword.add_root(name=new_tag))

        for tag in tag_objs:
            try:
                self.through.objects.get_or_create(
                    tag=tag, **self._lookup_kwargs())
            except Exception as e:
                logger.exception(e)


class Thesaurus(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """
    identifier = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True)

    # read from the RDF file
    title = models.CharField(max_length=255, null=False, blank=False)
    # read from the RDF file
    date = models.CharField(max_length=20, default='')
    # read from the RDF file
    description = models.TextField(max_length=255, default='')

    slug = models.CharField(max_length=64, default='')

    def __unicode__(self):
        return u"{0}".format(self.identifier)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = 'Thesauri'


class ThesaurusKeyword(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """
    # read from the RDF file
    about = models.CharField(max_length=255, null=True, blank=True)
    # read from the RDF file
    alt_label = models.CharField(
        max_length=255,
        default='',
        null=True,
        blank=True)

    thesaurus = models.ForeignKey('Thesaurus', related_name='thesaurus')

    def __unicode__(self):
        return u"{0}".format(self.alt_label)

    class Meta:
        ordering = ("alt_label",)
        verbose_name_plural = 'Thesaurus Keywords'
        unique_together = (("thesaurus", "alt_label"),)


class ThesaurusKeywordLabel(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """

    # read from the RDF file
    lang = models.CharField(max_length=3)
    # read from the RDF file
    label = models.CharField(max_length=255)
#    note  = models.CharField(max_length=511)

    keyword = models.ForeignKey('ThesaurusKeyword', related_name='keyword')

    def __unicode__(self):
        return u"{0}".format(self.label)

    class Meta:
        ordering = ("keyword", "lang")
        verbose_name_plural = 'Labels'
        unique_together = (("keyword", "lang"),)


class ResourceBaseManager(PolymorphicManager):
    def admin_contact(self):
        # this assumes there is at least one superuser
        superusers = get_user_model().objects.filter(is_superuser=True).order_by('id')
        if superusers.count() == 0:
            raise RuntimeError(
                'GeoNode needs at least one admin/superuser set')

        return superusers[0]

    def get_queryset(self):
        return super(
            ResourceBaseManager,
            self).get_queryset().non_polymorphic()

    def polymorphic_queryset(self):
        return super(ResourceBaseManager, self).get_queryset()


class ResourceBase(PolymorphicModel, PermissionLevelMixin, ItemBase):
    """
    Base Resource Object loosely based on ISO 19115:2003
    """

    VALID_DATE_TYPES = [(x.lower(), _(x))
                        for x in ['Creation', 'Publication', 'Revision']]

    date_help_text = _('reference date for the cited resource')
    date_type_help_text = _('identification of when a given event occurred')
    edition_help_text = _('version of the cited resource')
    abstract_help_text = _(
        'brief narrative summary of the content of the resource(s)')
    purpose_help_text = _(
        'summary of the intentions with which the resource(s) was developed')
    maintenance_frequency_help_text = _(
        'frequency with which modifications and deletions are made to the data after '
        'it is first produced')
    keywords_help_text = _(
        'commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject '
        '(space or comma-separated')
    tkeywords_help_text = _(
        'formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject '
        '(space or comma-separated')
    regions_help_text = _('keyword identifies a location')
    restriction_code_type_help_text = _(
        'limitation(s) placed upon the access or use of the data.')
    constraints_other_help_text = _(
        'other restrictions and legal prerequisites for accessing and using the resource or'
        ' metadata')
    license_help_text = _('license of the dataset')
    language_help_text = _('language used within the dataset')
    category_help_text = _(
        'high-level geographic data thematic classification to assist in the grouping and search of '
        'available geographic data sets.')
    spatial_representation_type_help_text = _(
        'method used to represent geographic information in the dataset.')
    temporal_extent_start_help_text = _(
        'time period covered by the content of the dataset (start)')
    temporal_extent_end_help_text = _(
        'time period covered by the content of the dataset (end)')
    data_quality_statement_help_text = _(
        'general explanation of the data producer\'s knowledge about the lineage of a'
        ' dataset')
    # internal fields
    uuid = models.CharField(max_length=36)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name='owned_resource',
        verbose_name=_("Owner"))
    contacts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ContactRole')
    title = models.CharField(_('title'), max_length=255, help_text=_(
        'name by which the cited resource is known'))
    alternate = models.CharField(max_length=128, null=True, blank=True)
    date = models.DateTimeField(
        _('date'),
        default=now,
        help_text=date_help_text)
    date_type = models.CharField(
        _('date type'),
        max_length=255,
        choices=VALID_DATE_TYPES,
        default='publication',
        help_text=date_type_help_text)
    edition = models.CharField(
        _('edition'),
        max_length=255,
        blank=True,
        null=True,
        help_text=edition_help_text)
    abstract = models.TextField(
        _('abstract'),
        max_length=2000,
        blank=True,
        help_text=abstract_help_text)
    purpose = models.TextField(
        _('purpose'),
        max_length=500,
        null=True,
        blank=True,
        help_text=purpose_help_text)
    maintenance_frequency = models.CharField(
        _('maintenance frequency'),
        max_length=255,
        choices=UPDATE_FREQUENCIES,
        blank=True,
        null=True,
        help_text=maintenance_frequency_help_text)

    keywords = TaggableManager(
        _('keywords'),
        through=TaggedContentItem,
        blank=True,
        help_text=keywords_help_text,
        manager=_HierarchicalTagManager)
    tkeywords = models.ManyToManyField(
        ThesaurusKeyword,
        help_text=tkeywords_help_text,
        blank=True)
    regions = models.ManyToManyField(
        Region,
        verbose_name=_('keywords region'),
        blank=True,
        help_text=regions_help_text)

    restriction_code_type = models.ForeignKey(
        RestrictionCodeType,
        verbose_name=_('restrictions'),
        help_text=restriction_code_type_help_text,
        null=True,
        blank=True,
        limit_choices_to=Q(
            is_choice=True))

    constraints_other = models.TextField(
        _('restrictions other'),
        blank=True,
        null=True,
        help_text=constraints_other_help_text)

    license = models.ForeignKey(License, null=True, blank=True,
                                verbose_name=_("License"),
                                help_text=license_help_text)
    language = models.CharField(
        _('language'),
        max_length=3,
        choices=ALL_LANGUAGES,
        default='eng',
        help_text=language_help_text)

    category = models.ForeignKey(
        TopicCategory,
        null=True,
        blank=True,
        limit_choices_to=Q(
            is_choice=True),
        help_text=category_help_text)

    spatial_representation_type = models.ForeignKey(
        SpatialRepresentationType,
        null=True,
        blank=True,
        limit_choices_to=Q(
            is_choice=True),
        verbose_name=_("spatial representation type"),
        help_text=spatial_representation_type_help_text)

    # Section 5
    temporal_extent_start = models.DateTimeField(
        _('temporal extent start'),
        blank=True,
        null=True,
        help_text=temporal_extent_start_help_text)
    temporal_extent_end = models.DateTimeField(
        _('temporal extent end'),
        blank=True,
        null=True,
        help_text=temporal_extent_end_help_text)

    supplemental_information = models.TextField(
        _('supplemental information'),
        max_length=2000,
        default=DEFAULT_SUPPLEMENTAL_INFORMATION,
        help_text=_('any other descriptive information about the dataset'))

    # Section 8
    data_quality_statement = models.TextField(
        _('data quality statement'),
        max_length=2000,
        blank=True,
        null=True,
        help_text=data_quality_statement_help_text)

    group = models.ForeignKey(Group, null=True, blank=True)

    # Section 9
    # see metadata_author property definition below

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images
    # and metadata records.
    bbox_x0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_x1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    bbox_y1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True)
    srid = models.CharField(
        max_length=30,
        blank=False,
        null=False,
        default='EPSG:4326')

    # CSW specific fields
    csw_typename = models.CharField(
        _('CSW typename'),
        max_length=32,
        default='gmd:MD_Metadata',
        null=False)

    csw_schema = models.CharField(_('CSW schema'),
                                  max_length=64,
                                  default='http://www.isotc211.org/2005/gmd',
                                  null=False)

    csw_mdsource = models.CharField(
        _('CSW source'),
        max_length=256,
        default='local',
        null=False)
    csw_insert_date = models.DateTimeField(
        _('CSW insert date'), auto_now_add=True, null=True)
    csw_type = models.CharField(
        _('CSW type'),
        max_length=32,
        default='dataset',
        null=False,
        choices=HIERARCHY_LEVELS)
    csw_anytext = models.TextField(_('CSW anytext'), null=True, blank=True)
    csw_wkt_geometry = models.TextField(
        _('CSW WKT geometry'),
        null=False,
        default='POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))')

    # metadata XML specific fields
    metadata_uploaded = models.BooleanField(default=False)
    metadata_uploaded_preserve = models.BooleanField(default=False)
    metadata_xml = models.TextField(
        null=True,
        default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>',
        blank=True)

    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    featured = models.BooleanField(_("Featured"), default=False, help_text=_(
        'Should this resource be advertised in home page?'))
    is_published = models.BooleanField(
        _("Is Published"),
        default=True,
        help_text=_('Should this resource be published and searchable?'))
    is_approved = models.BooleanField(
        _("Approved"),
        default=True,
        help_text=_('Is this resource validated from a publisher or editor?'))

    # fields necessary for the apis
    thumbnail_url = models.TextField(null=True, blank=True)
    detail_url = models.CharField(max_length=255, null=True, blank=True)
    rating = models.IntegerField(default=0, null=True, blank=True)

    def __unicode__(self):
        return self.title

    def get_upload_session(self):
        raise NotImplementedError()

    @property
    def group_name(self):
        if self.group:
            return str(self.group)
        return None

    @property
    def bbox(self):
        """BBOX is in the format: [x0,x1,y0,y1]."""
        return [
            self.bbox_x0,
            self.bbox_x1,
            self.bbox_y0,
            self.bbox_y1,
            self.srid]

    @property
    def bbox_string(self):
        """BBOX is in the format: [x0,y0,x1,y1]."""
        return ",".join([str(self.bbox_x0), str(self.bbox_y0),
                         str(self.bbox_x1), str(self.bbox_y1)])

    @property
    def geographic_bounding_box(self):
        """BBOX is in the format: [x0,x1,y0,y1]."""
        return bbox_to_wkt(
            self.bbox_x0,
            self.bbox_x1,
            self.bbox_y0,
            self.bbox_y1,
            srid=self.srid)

    @property
    def license_light(self):
        a = []
        if not self.license:
            return ''
        if (not (self.license.name is None)) and (len(self.license.name) > 0):
            a.append(self.license.name)
        if (not (self.license.url is None)) and (len(self.license.url) > 0):
            a.append("(" + self.license.url + ")")
        return " ".join(a)

    @property
    def license_verbose(self):
        a = []
        if (not (self.license.name_long is None)) and (
                len(self.license.name_long) > 0):
            a.append(self.license.name_long + ":")
        if (not (self.license.description is None)) and (
                len(self.license.description) > 0):
            a.append(self.license.description)
        if (not (self.license.url is None)) and (len(self.license.url) > 0):
            a.append("(" + self.license.url + ")")
        return " ".join(a)

    @property
    def metadata_completeness(self):
        required_fields = [
            'abstract',
            'category',
            'data_quality_statement',
            'date',
            'date_type',
            'language',
            'license',
            'regions',
            'title']
        if self.restriction_code_type == 'otherRestrictions':
            required_fields.append('constraints_other')
        filled_fields = []
        for required_field in required_fields:
            field = getattr(self, required_field, None)
            if field:
                if required_field is 'license':
                    if field.name is 'Not Specified':
                        continue
                if required_field is 'regions':
                    if not field.all():
                        continue
                if required_field is 'category':
                    if not field.identifier:
                        continue
                filled_fields.append(field)
        return '{}%'.format(len(filled_fields) * 100 / len(required_fields))

    def keyword_list(self):
        return [kw.name for kw in self.keywords.all()]

    def keyword_slug_list(self):
        return [kw.slug for kw in self.keywords.all()]

    def region_name_list(self):
        return [region.name for region in self.regions.all()]

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
        keywords_qs = self.get_real_instance().keywords.all()
        if keywords_qs:
            return ','.join([kw.name for kw in keywords_qs])
        else:
            return ''

    def set_bounds_from_center_and_zoom(self, center_x, center_y, zoom):
        """
        Calculate zoom level and center coordinates in mercator.
        """
        self.center_x = center_x
        self.center_y = center_y
        self.zoom = zoom

        deg_len_equator = 40075160 / 360

        # covert center in lat lon
        def get_lon_lat():
            wgs84 = Proj(init='epsg:4326')
            mercator = Proj(init='epsg:3857')
            lon, lat = transform(mercator, wgs84, center_x, center_y)
            return lon, lat

        # calculate the degree length at this latitude
        def deg_len():
            lon, lat = get_lon_lat()
            return math.cos(lat) * deg_len_equator

        lon, lat = get_lon_lat()

        # taken from http://wiki.openstreetmap.org/wiki/Zoom_levels
        # it might be not precise but enough for the purpose
        distance_per_pixel = 40075160 * math.cos(lat) / 2**(zoom + 8)

        # calculate the distance from the center of the map in degrees
        # we use the calculated degree length on the x axis and the
        # normal degree length on the y axis assumin that it does not change

        # Assuming a map of 1000 px of width and 700 px of height
        distance_x_degrees = distance_per_pixel * 500 / deg_len()
        distance_y_degrees = distance_per_pixel * 350 / deg_len_equator

        self.bbox_x0 = lon - distance_x_degrees
        self.bbox_x1 = lon + distance_x_degrees
        self.bbox_y0 = lat - distance_y_degrees
        self.bbox_y1 = lat + distance_y_degrees

    def set_bounds_from_bbox(self, bbox, srid):
        """
        Calculate zoom level and center coordinates in mercator.

        :param bbox: BBOX is in the  format: [x0, x1, y0, y1], which is:
            [min lon, max lon, min lat, max lat] or
            [xmin, xmax, ymin, ymax]
        :type bbox: list
        """
        if not bbox or len(bbox) < 4:
            raise ValidationError(
                'Bounding Box cannot be empty %s for a given resource' %
                self.name)
        if not srid:
            raise ValidationError(
                'Projection cannot be empty %s for a given resource' %
                self.name)
        self.bbox_x0 = bbox[0]
        self.bbox_x1 = bbox[1]
        self.bbox_y0 = bbox[2]
        self.bbox_y1 = bbox[3]
        self.srid = srid

        minx, maxx, miny, maxy = [float(c) for c in bbox]
        x = (minx + maxx) / 2
        y = (miny + maxy) / 2
        (center_x, center_y) = forward_mercator((x, y))

        xdiff = maxx - minx
        ydiff = maxy - miny

        zoom = 0

        if xdiff > 0 and ydiff > 0:
            width_zoom = math.log(360 / xdiff, 2)
            height_zoom = math.log(360 / ydiff, 2)
            zoom = math.ceil(min(width_zoom, height_zoom))

        self.zoom = zoom
        self.center_x = center_x
        self.center_y = center_y

    def download_links(self):
        """assemble download links for pycsw"""
        links = []
        for url in self.link_set.all():
            if url.link_type == 'metadata':  # avoid recursion
                continue
            if url.link_type == 'html':
                links.append(
                    (self.title,
                     'Web address (URL)',
                     'WWW:LINK-1.0-http--link',
                     url.url))
            elif url.link_type in ('OGC:WMS', 'OGC:WFS', 'OGC:WCS'):
                links.append((self.title, url.name, url.link_type, url.url))
            else:
                description = '%s (%s Format)' % (self.title, url.name)
                links.append(
                    (self.title,
                     description,
                     'WWW:DOWNLOAD-1.0-http--download',
                     url.url))
        return links

    def get_tiles_url(self):
        """Return URL for Z/Y/X mapping clients or None if it does not exist.
        """
        try:
            tiles_link = self.link_set.get(name='Tiles')
        except Link.DoesNotExist:
            return None
        else:
            return tiles_link.url

    def get_legend(self):
        """Return Link for legend or None if it does not exist.
        """
        try:
            legends_link = self.link_set.get(name='Legend')
        except Link.DoesNotExist:
            return None
        except Link.MultipleObjectsReturned:
            return None
        else:
            return legends_link

    def get_legend_url(self):
        """Return URL for legend or None if it does not exist.

           The legend can be either an image (for Geoserver's WMS)
           or a JSON object for ArcGIS.
        """
        legend = self.get_legend()

        if legend is None:
            return None

        return legend.url

    def get_ows_url(self):
        """Return URL for OGC WMS server None if it does not exist.
        """
        try:
            ows_link = self.link_set.get(name='OGC:WMS')
        except Link.DoesNotExist:
            return None
        else:
            return ows_link.url

    def get_thumbnail_url(self):
        """Return a thumbnail url.

           It could be a local one if it exists, a remote one (WMS GetImage) for example
           or a 'Missing Thumbnail' one.
        """
        local_thumbnails = self.link_set.filter(name='Thumbnail')
        if local_thumbnails.count() > 0:
            return local_thumbnails[0].url

        remote_thumbnails = self.link_set.filter(name='Remote Thumbnail')
        if remote_thumbnails.count() > 0:
            return remote_thumbnails[0].url

        return staticfiles.static(settings.MISSING_THUMBNAIL)

    def has_thumbnail(self):
        """Determine if the thumbnail object exists and an image exists"""
        return self.link_set.filter(name='Thumbnail').exists()

    # Note - you should probably broadcast layer#post_save() events to ensure
    # that indexing (or other listeners) are notified
    def save_thumbnail(self, filename, image):
        upload_to = 'thumbs/'
        upload_path = os.path.join('thumbs/', filename)

        try:

            if storage.exists(upload_path):
                # Delete if exists otherwise the (FileSystemStorage) implementation
                # will create a new file with a unique name
                storage.delete(os.path.join(upload_path))

            storage.save(upload_path, ContentFile(image))

            url_path = os.path.join(
                settings.MEDIA_URL,
                upload_to,
                filename).replace(
                '\\',
                '/')
            url = urljoin(settings.SITEURL, url_path)

            # should only have one 'Thumbnail' link
            obj, created = Link.objects.get_or_create(resource=self,
                                                      name='Thumbnail',
                                                      defaults=dict(
                                                          url=url,
                                                          extension='png',
                                                          mime='image/png',
                                                          link_type='image',
                                                      ))
            self.thumbnail_url = url
            obj.url = url
            obj.save()

            ResourceBase.objects.filter(id=self.id).update(
                thumbnail_url=url
            )

        except Exception:
            logger.error(
                'Error when generating the thumbnail for resource %s.' %
                self.id)
            logger.error('Check permissions for file %s.' % upload_path)

    def set_missing_info(self):
        """Set default permissions and point of contacts.

           It is mandatory to call it from descendant classes
           but hard to enforce technically via signals or save overriding.
        """
        from guardian.models import UserObjectPermission
        logger.debug('Checking for permissions.')
        #  True if every key in the get_all_level_info dict is empty.
        no_custom_permissions = UserObjectPermission.objects.filter(
            content_type=ContentType.objects.get_for_model(
                self.get_self_resource()), object_pk=str(
                self.pk)).exists()

        if not no_custom_permissions:
            logger.debug(
                'There are no permissions for this object, setting default perms.')
            self.set_default_permissions()

        user = None
        if self.owner:
            user = self.owner
        else:
            try:
                user = ResourceBase.objects.admin_contact().user
            except BaseException:
                pass

        if user:
            if self.poc is None:
                self.poc = user
            if self.metadata_author is None:
                self.metadata_author = user

    def maintenance_frequency_title(self):
        return [v for i, v in enumerate(
            UPDATE_FREQUENCIES) if v[0] == self.maintenance_frequency][0][1].title()

    def language_title(self):
        return [v for i, v in enumerate(
            ALL_LANGUAGES) if v[0] == self.language][0][1].title()

    def _set_poc(self, poc):
        # reset any poc assignation to this resource
        ContactRole.objects.filter(
            role='pointOfContact',
            resource=self).delete()
        # create the new assignation
        ContactRole.objects.create(
            role='pointOfContact',
            resource=self,
            contact=poc)

    def _get_poc(self):
        try:
            the_poc = ContactRole.objects.get(
                role='pointOfContact', resource=self).contact
        except ContactRole.DoesNotExist:
            the_poc = None
        return the_poc

    poc = property(_get_poc, _set_poc)

    def _set_metadata_author(self, metadata_author):
        # reset any metadata_author assignation to this resource
        ContactRole.objects.filter(role='author', resource=self).delete()
        # create the new assignation
        ContactRole.objects.create(
            role='author',
            resource=self,
            contact=metadata_author)

    def _get_metadata_author(self):
        try:
            the_ma = ContactRole.objects.get(
                role='author', resource=self).contact
        except ContactRole.DoesNotExist:
            the_ma = None
        return the_ma

    def handle_moderated_uploads(self):
        if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
            self.is_approved = False
            self.is_published = False

    metadata_author = property(_get_metadata_author, _set_metadata_author)

    objects = ResourceBaseManager()

    class Meta:
        # custom permissions,
        # add, change and delete are standard in django-guardian
        permissions = (
            ('view_resourcebase', 'Can view resource'),
            ('change_resourcebase_permissions', 'Can change resource permissions'),
            ('download_resourcebase', 'Can download resource'),
            ('publish_resourcebase', 'Can publish resource'),
            ('change_resourcebase_metadata', 'Can change resource metadata'),
        )


class LinkManager(models.Manager):
    """Helper class to access links grouped by type
    """

    def data(self):
        return self.get_queryset().filter(link_type='data')

    def image(self):
        return self.get_queryset().filter(link_type='image')

    def download(self):
        return self.get_queryset().filter(link_type__in=['image', 'data', 'original'])

    def metadata(self):
        return self.get_queryset().filter(link_type='metadata')

    def original(self):
        return self.get_queryset().filter(link_type='original')

    def geogig(self):
        return self.get_queryset().filter(name__icontains='geogig')

    def ows(self):
        return self.get_queryset().filter(
            link_type__in=['OGC:WMS', 'OGC:WFS', 'OGC:WCS'])


class Link(models.Model):
    """Auxiliary model for storing links for resources.

       This helps avoiding the need for runtime lookups
       to the OWS server or the CSW Catalogue.

       There are four types of links:
        * original: For uploaded files (Shapefiles or GeoTIFFs)
        * data: For WFS and WCS links that allow access to raw data
        * image: For WMS and TMS links
        * metadata: For CSW links
        * OGC:WMS: for WMS service links
        * OGC:WFS: for WFS service links
        * OGC:WCS: for WCS service links
    """
    resource = models.ForeignKey(ResourceBase, blank=True, null=True)
    extension = models.CharField(
        max_length=255,
        help_text=_('For example "kml"'))
    link_type = models.CharField(
        max_length=255, choices=[
            (x, x) for x in LINK_TYPES])
    name = models.CharField(max_length=255, help_text=_(
        'For example "View in Google Earth"'))
    mime = models.CharField(max_length=255,
                            help_text=_('For example "text/xml"'))
    url = models.TextField(max_length=1000)

    objects = LinkManager()

    def __str__(self):
        return '%s link' % self.link_type


def resourcebase_post_save(instance, *args, **kwargs):
    """
    Used to fill any additional fields after the save.
    Has to be called by the children
    """
    # we need to remove stale links
    for link in instance.link_set.all():
        if link.name == "External Document":
            if link.resource.doc_url != link.url:
                link.delete()
        else:
            if urlsplit(settings.SITEURL).hostname not in link.url:
                link.delete()

    try:
        # set default License if no specified
        if instance.license is None:
            license = License.objects.filter(name="Not Specified")

            if license and len(license) > 0:
                instance.license = license[0]

        ResourceBase.objects.filter(id=instance.id).update(
            thumbnail_url=instance.get_thumbnail_url(),
            detail_url=instance.get_absolute_url(),
            csw_insert_date=now(),
            license=instance.license)
        instance.refresh_from_db()
    except BaseException:
        tb = traceback.format_exc()
        if tb:
            logger.debug(tb)
    finally:
        instance.set_missing_info()

    try:
        if instance.regions and instance.regions.all():
            """
            try:
                queryset = instance.regions.all().order_by('name')
                for region in queryset:
                    print ("%s : %s" % (region.name, region.geographic_bounding_box))
            except:
                tb = traceback.format_exc()
            else:
                tb = None
            finally:
                if tb:
                    logger.debug(tb)
            """
            pass
        else:
            srid1, wkt1 = instance.geographic_bounding_box.split(";")
            srid1 = re.findall(r'\d+', srid1)

            poly1 = GEOSGeometry(wkt1, srid=int(srid1[0]))
            poly1.transform(4326)

            queryset = Region.objects.all().order_by('name')
            global_regions = []
            regions_to_add = []
            for region in queryset:
                try:
                    srid2, wkt2 = region.geographic_bounding_box.split(";")
                    srid2 = re.findall(r'\d+', srid2)

                    poly2 = GEOSGeometry(wkt2, srid=int(srid2[0]))
                    poly2.transform(4326)

                    if poly2.intersection(poly1):
                        regions_to_add.append(region)
                    if region.level == 0 and region.parent is None:
                        global_regions.append(region)
                except BaseException:
                    tb = traceback.format_exc()
                    if tb:
                        logger.debug(tb)
            if regions_to_add or global_regions:
                if regions_to_add and len(
                        regions_to_add) > 0 and len(regions_to_add) <= 30:
                    instance.regions.add(*regions_to_add)
                else:
                    instance.regions.add(*global_regions)
    except BaseException:
        tb = traceback.format_exc()
        if tb:
            logger.debug(tb)


def rating_post_save(instance, *args, **kwargs):
    """
    Used to fill the average rating field on OverallRating change.
    """
    ResourceBase.objects.filter(
        id=instance.object_id).update(
        rating=instance.rating)


signals.post_save.connect(rating_post_save, sender=OverallRating)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def do_login(sender, user, request, **kwargs):
    """
    Take action on user login. Generate a new user access_token to be shared
    with GeoServer, and store it into the request.session
    """
    if user and user.is_authenticated():
        token = None
        try:
            Application = get_application_model()
            app = Application.objects.get(name="GeoServer")

            # Lets create a new one
            token = generate_token()

            AccessToken.objects.get_or_create(
                user=user,
                application=app,
                expires=datetime.datetime.now(timezone.get_current_timezone()) +
                datetime.timedelta(
                    days=1),
                token=token)
        except BaseException:
            u = uuid.uuid1()
            token = u.hex

        # Do GeoServer Login
        url = "%s%s&access_token=%s" % (settings.OGC_SERVER['default']['LOCATION'],
                                        'ows?service=wms&version=1.3.0&request=GetCapabilities',
                                        token)

        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        jsessionid = None
        try:
            opener.open(url)
            for c in cj:
                if c.name == "JSESSIONID":
                    jsessionid = c.value
        except BaseException:
            u = uuid.uuid1()
            jsessionid = u.hex

        request.session['access_token'] = token
        request.session['JSESSIONID'] = jsessionid


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def do_logout(sender, user, request, **kwargs):
    """
    Take action on user logout. Cleanup user access_token and send logout
    request to GeoServer
    """
    if 'access_token' in request.session:
        try:
            Application = get_application_model()
            app = Application.objects.get(name="GeoServer")

            # Lets delete the old one
            try:
                old = AccessToken.objects.get(user=user, application=app)
            except BaseException:
                pass
            else:
                old.delete()
        except BaseException:
            pass

        # Do GeoServer Logout
        if 'access_token' in request.session:
            access_token = request.session['access_token']
        else:
            access_token = None

        if access_token:
            url = "%s%s?access_token=%s" % (settings.OGC_SERVER['default']['LOCATION'],
                                            settings.OGC_SERVER['default']['LOGOUT_ENDPOINT'],
                                            access_token)
            header_params = {
                "Authorization": ("Bearer %s" % access_token)
            }
        else:
            url = "%s%s" % (settings.OGC_SERVER['default']['LOCATION'],
                            settings.OGC_SERVER['default']['LOGOUT_ENDPOINT'])

        param = {}
        data = urllib.urlencode(param)

        cookies = None
        for cook in request.COOKIES:
            name = str(cook)
            value = request.COOKIES.get(name)
            if name == 'csrftoken':
                header_params['X-CSRFToken'] = value

            cook = "%s=%s" % (name, value)
            if not cookies:
                cookies = cook
            else:
                cookies = cookies + '; ' + cook

        if cookies:
            if 'JSESSIONID' in request.session and request.session['JSESSIONID']:
                cookies = cookies + '; JSESSIONID=' + \
                    request.session['JSESSIONID']
            header_params['Cookie'] = cookies

        gs_request = urllib2.Request(url, data, header_params)

        try:
            urllib2.urlopen(gs_request)
        except BaseException:
            tb = traceback.format_exc()
            if tb:
                logger.debug(tb)

        if 'access_token' in request.session:
            del request.session['access_token']

        request.session.modified = True


user_logged_in.connect(do_login)
user_logged_out.connect(do_logout)
