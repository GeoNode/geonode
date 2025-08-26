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

import os
import re
import html
import math
import uuid
import logging
import traceback
from typing import List, Optional, Union, Tuple
from sequences.models import Sequence
from sequences import get_next_value
from PIL import Image

from django.db import transaction
from django.db import models
from django.db.models import Max
from django.conf import settings
from django.utils.html import escape
from django.utils.timezone import now
from django.db.models import Q, signals
from django.db.utils import IntegrityError, OperationalError
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.db.models.fields.json import JSONField
from django.utils.functional import cached_property, classproperty
from django.contrib.gis.geos import GEOSGeometry, Polygon, Point
from django.contrib.gis.db.models import PolygonField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager

from taggit.models import TagBase, ItemBase
from taggit.managers import TaggableManager, _TaggableManager

from guardian.shortcuts import get_anonymous_user, get_objects_for_user
from treebeard.mp_tree import MP_Node, MP_NodeQuerySet, MP_NodeManager
from geonode import GeoNodeException

from geonode.base import enumerations
from geonode.singleton import SingletonModel
from geonode.groups.conf import settings as groups_settings
from geonode.base.bbox_utils import BBOXHelper, polygon_from_bbox
from geonode.utils import (
    bbox_to_wkt,
    find_by_attr,
    bbox_to_projection,
    bbox_swap,
    get_allowed_extensions,
    is_monochromatic_image,
)
from geonode.thumbs.utils import thumb_size, remove_thumbs, get_unique_upload_path, ThumbnailAlgorithms
from geonode.groups.models import GroupProfile
from geonode.security.utils import get_visible_resources, get_geoapp_subtypes
from geonode.security.models import PermissionLevelMixin
from geonode.security.permissions import VIEW_PERMISSIONS, OWNER_PERMISSIONS

from geonode.notifications_helper import send_notification, get_notification_recipients
from geonode.people import Roles
from geonode.people.enumerations import ROLE_VALUES

from urllib.parse import urlsplit, urljoin
from geonode.storage.manager import storage_manager

logger = logging.getLogger(__name__)


class ContactRole(models.Model):
    """
    ContactRole is an intermediate model to bind Profiles as Contacts to Resources and apply roles.
    """

    resource = models.ForeignKey("ResourceBase", blank=False, null=False, on_delete=models.CASCADE)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(
        choices=ROLE_VALUES, max_length=255, help_text=_("function performed by the responsible " "party")
    )

    class Meta:
        unique_together = (("contact", "resource", "role"),)


class TopicCategory(models.Model):
    """
    Metadata about high-level geographic data thematic classification.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_MD_TopicCategoryCode">
    """

    identifier = models.CharField(max_length=255, default="location")
    description = models.TextField(default="")
    gn_description = models.TextField("GeoNode description", default="", null=True)
    is_choice = models.BooleanField(default=True)
    fa_class = models.CharField(max_length=64, default="fa-times")

    def __str__(self):
        return self.gn_description

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = "Metadata Topic Categories"


class SpatialRepresentationType(models.Model):
    """
    Metadata information about the spatial representation type.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_SpatialRepresentationTypeCode">
    """

    identifier = models.CharField(max_length=255, editable=False)
    description = models.CharField(max_length=255, editable=False)
    gn_description = models.CharField("GeoNode description", max_length=255)
    is_choice = models.BooleanField(default=True)

    def __str__(self):
        return str(self.gn_description)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = "Metadata Spatial Representation Types"


class Region(MPTTModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    parent = TreeForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images
    # and metadata records.
    bbox_x0 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    bbox_x1 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    bbox_y0 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    bbox_y1 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    srid = models.CharField(max_length=30, blank=False, null=False, default="EPSG:4326")

    def __str__(self):
        return str(self.name)

    @property
    def bbox(self):
        """BBOX is in the format: [x0,x1,y0,y1]."""
        return [self.bbox_x0, self.bbox_x1, self.bbox_y0, self.bbox_y1, self.srid]

    @property
    def bbox_string(self):
        """BBOX is in the format: [x0,y0,x1,y1]."""
        return ",".join([str(self.bbox_x0), str(self.bbox_y0), str(self.bbox_x1), str(self.bbox_y1)])

    @property
    def geographic_bounding_box(self):
        """BBOX is in the format: [x0,x1,y0,y1]."""
        return bbox_to_wkt(self.bbox_x0, self.bbox_x1, self.bbox_y0, self.bbox_y1, srid=self.srid)

    @property
    def geom(self):
        srid, wkt = self.geographic_bounding_box.split(";")
        srid = re.findall(r"\d+", srid)
        geom = GEOSGeometry(wkt, srid=int(srid[0]))
        geom.transform(4326)
        return geom

    def is_assignable_to_geom(self, extent_geom: GEOSGeometry):
        region_geom = self.geom

        if region_geom.contains(extent_geom) or region_geom.overlaps(extent_geom):
            return True
        return False

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Metadata Regions"

    class MPTTMeta:
        order_insertion_by = ["name"]


class RestrictionCodeType(models.Model):
    """
    Metadata information about the spatial representation type.
    It should reflect a list of codes from TC211
    See: http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    <CodeListDictionary gml:id="MD_RestrictionCode">
    """

    identifier = models.CharField(max_length=255, editable=False)
    description = models.TextField(max_length=255, editable=False)
    gn_description = models.TextField("GeoNode description", max_length=255)
    is_choice = models.BooleanField(default=True)

    def __str__(self):
        return str(self.gn_description)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = "Metadata Restriction Code Types"


class License(models.Model):
    identifier = models.CharField(max_length=255, editable=False)
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    license_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.name)

    @property
    def name_long(self):
        if self.abbreviation is None or len(self.abbreviation) == 0:
            return self.name
        else:
            return f"{self.name} ({self.abbreviation})"

    @property
    def description_bullets(self):
        if self.description is None or len(self.description) == 0:
            return ""
        else:
            bullets = []
            lines = self.description.split("\n")
            for line in lines:
                bullets.append(f"+ {line}")
            return bullets

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Licenses"


class HierarchicalKeywordQuerySet(MP_NodeQuerySet):
    """QuerySet to automatically create a root node if `depth` not given."""

    def create(self, **kwargs):
        if "depth" not in kwargs:
            return self.model.add_root(**kwargs)
        return super().create(**kwargs)


class HierarchicalKeywordManager(MP_NodeManager):
    def get_queryset(self):
        return HierarchicalKeywordQuerySet(self.model).order_by("path")


class HierarchicalKeyword(TagBase, MP_Node):
    node_order_by = ["name"]
    objects = HierarchicalKeywordManager()

    @classmethod
    def resource_keywords_tree(cls, user, parent=None, resource_type=None, resource_name=None):
        """Returns resource keywords tree as a dict object."""
        user = user or get_anonymous_user()
        resource_types = [resource_type] if resource_type else ["dataset", "map", "document"] + get_geoapp_subtypes()
        qset = cls.get_tree(parent)

        if settings.SKIP_PERMS_FILTER:
            resources = ResourceBase.objects.all()
        else:
            resources = get_objects_for_user(user, "base.view_resourcebase")

        resources = resources.filter(
            polymorphic_ctype__model__in=resource_types,
        )

        if resource_name is not None:
            resources = resources.filter(title=resource_name)

        resources = get_visible_resources(
            resources,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
        )

        tree = {}

        for hkw in qset.order_by("name"):
            slug = hkw.slug
            tags_count = 0

            tags_count = TaggedContentItem.objects.filter(content_object__in=resources, tag=hkw).count()

            if tags_count > 0:
                newobj = {"id": hkw.pk, "text": hkw.name, "href": slug, "tags": [tags_count]}
                depth = hkw.depth or 1

                # No use case, so purpose of 'parent' param is not clear.
                # So following first 'if' statement is left unchanged
                if (not parent and depth == 1) or (parent and depth == parent.depth):
                    if hkw.pk not in tree:
                        tree[hkw.pk] = newobj
                        tree[hkw.pk]["nodes"] = []
                    else:
                        tree[hkw.pk]["tags"] = [tags_count]
                else:
                    tree = cls._keywords_tree_of_a_child(hkw, tree, newobj)

        return list(tree.values())

    @classmethod
    def _keywords_tree_of_a_child(cls, child, tree, newobj):
        qs = cls.get_tree(child.get_root())
        parent = qs[0]

        if parent.id not in tree:
            tree[parent.id] = {"id": parent.id, "text": parent.name, "href": parent.slug, "tags": [], "nodes": []}

        node = tree[parent.id]

        for kw in qs:
            if child.is_descendant_of(kw):
                if kw.depth > 1:
                    item_found = None
                    if node["nodes"]:
                        item_found = find_by_attr(node["nodes"], kw.id)

                    if item_found is None:
                        node["nodes"].append({"id": kw.id, "text": kw.name, "href": kw.slug, "nodes": []})
                        node = node["nodes"][-1]
                    else:
                        node = item_found
                        node["nodes"] = getattr(node, "nodes", [])

        # All leaves appended but a child which is not a leaf may not be added
        # again, as a leaf, but only its tag count be updated
        item_found = find_by_attr(node["nodes"], newobj["id"])
        if item_found is not None:
            item_found["tags"] = newobj["tags"]
        else:
            node["nodes"].append(newobj)

        return tree


class TaggedContentItem(ItemBase):
    content_object = models.ForeignKey("ResourceBase", on_delete=models.CASCADE)
    tag = models.ForeignKey("HierarchicalKeyword", related_name="keywords", on_delete=models.CASCADE)

    # see https://github.com/alex/django-taggit/issues/101
    @classmethod
    def tags_for(cls, model, instance=None, **extra_filters):
        kwargs = extra_filters or {}
        if instance is not None:
            return cls.tag_model().objects.filter(**{f"{cls.tag_relname()}__content_object": instance}, **kwargs)
        return (
            cls.tag_model()
            .objects.filter(**{f"{cls.tag_relname()}__content_object__isnull": False}, **kwargs)
            .distinct()
        )


class _HierarchicalTagManager(_TaggableManager):
    def add(self, *tags, through_defaults=None, tag_kwargs=None):
        if tag_kwargs is None:
            tag_kwargs = {}

        str_tags = set([t for t in tags if not isinstance(t, self.through.tag_model())])
        tag_objs = set(tags) - str_tags
        # If str_tags has 0 elements Django actually optimizes that to not do a
        # query.  Malcolm is very smart.
        try:
            existing = self.through.tag_model().objects.filter(name__in=str_tags, **tag_kwargs).all()
            tag_objs.update(existing)
            new_ids = set()
            _new_keywords = str_tags - set(t.name for t in existing)
            for new_tag in list(_new_keywords):
                new_tag = escape(new_tag)
                new_tag_obj = None
                with transaction.atomic():
                    try:
                        new_tag_obj = HierarchicalKeyword.add_root(name=new_tag)
                    except Exception as e:
                        logger.exception(e)
                # HierarchicalKeyword.add_root didn't return, probably the keyword already exists
                if not new_tag_obj:
                    new_tag_obj = HierarchicalKeyword.objects.filter(name=new_tag)
                    if new_tag_obj.exists():
                        new_tag_obj.first()
                if new_tag_obj:
                    tag_objs.add(new_tag_obj)
                    new_ids.add(new_tag_obj.id)
                else:
                    # Something has gone seriously wrong and we cannot assign the tag to the resource
                    logger.error(f"Error during the keyword creation for keyword: {new_tag}")

            signals.m2m_changed.send(
                sender=self.through,
                action="pre_add",
                instance=self.instance,
                reverse=False,
                model=self.through.tag_model(),
                pk_set=new_ids,
            )

            for tag in tag_objs:
                try:
                    self.through.objects.get_or_create(tag=tag, **self._lookup_kwargs(), defaults=through_defaults)
                except Exception as e:
                    logger.exception(e)

            signals.m2m_changed.send(
                sender=self.through,
                action="post_add",
                instance=self.instance,
                reverse=False,
                model=self.through.tag_model(),
                pk_set=new_ids,
            )
        except IntegrityError as e:
            logger.warning("The keyword provided already exists", exc_info=e)
        except OperationalError as e:
            logger.warning(
                "An error has occured with the DB connection. Please try to re-add the keywords again", exc_info=e
            )
        except Exception as e:
            raise e


class Thesaurus(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """

    id = models.AutoField(null=False, blank=False, unique=True, primary_key=True)

    identifier = models.CharField(max_length=255, null=False, blank=False, unique=True)

    # read from the RDF file
    title = models.CharField(max_length=255, null=False, blank=False)
    # read from the RDF file
    date = models.CharField(max_length=20, default="")
    # read from the RDF file
    description = models.TextField(max_length=255, default="")

    slug = models.CharField(max_length=64, default="", null=True, blank=True)

    about = models.CharField(max_length=255, null=True, blank=True)

    card_min = models.IntegerField(default=0)
    card_max = models.IntegerField(default=-1)
    facet = models.BooleanField(default=True)
    order = models.IntegerField(null=False, default=0)

    def __str__(self):
        return str(self.identifier)

    class Meta:
        ordering = ("identifier",)
        verbose_name_plural = "Thesauri"


class ThesaurusKeywordLabel(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """

    # read from the RDF file
    lang = models.CharField(max_length=10)
    # read from the RDF file
    label = models.CharField(max_length=255)
    # note  = models.CharField(max_length=511)

    keyword = models.ForeignKey("ThesaurusKeyword", related_name="keyword", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.label)

    class Meta:
        ordering = ("keyword", "lang")
        verbose_name_plural = "Thesaurus Keyword Labels"
        unique_together = (("keyword", "lang"),)


class ThesaurusKeyword(models.Model):
    """
    Loadable thesaurus containing keywords in different languages
    """

    # read from the RDF file
    about = models.CharField(max_length=255, null=True, blank=True)
    # read from the RDF file
    alt_label = models.CharField(max_length=255, default="", null=True, blank=True)

    thesaurus = models.ForeignKey("Thesaurus", related_name="thesaurus", on_delete=models.CASCADE)

    image = models.CharField(max_length=512, help_text="A URL to an image", null=True, blank=True)

    def __str__(self):
        return str(self.alt_label)

    @property
    def labels(self):
        return ThesaurusKeywordLabel.objects.filter(keyword=self)

    class Meta:
        ordering = ("alt_label",)
        verbose_name_plural = "Thesaurus Keywords"
        unique_together = (("thesaurus", "alt_label"),)


def generate_thesaurus_reference(instance, *args, **kwargs):
    if instance.about:
        return instance.about

    prefix = instance.thesaurus.about or f"{settings.SITEURL}/thesaurus/{instance.thesaurus.identifier}"
    suffix = instance.alt_label or instance.id
    instance.about = f"{prefix}#{suffix}"

    instance.save()
    return instance.about


signals.post_save.connect(generate_thesaurus_reference, sender=ThesaurusKeyword)


class ThesaurusLabel(models.Model):
    """
    Contains localized version of the thesaurus title
    """

    # read from the RDF file
    lang = models.CharField(max_length=10)
    # read from the RDF file
    label = models.CharField(max_length=255)

    thesaurus = models.ForeignKey("Thesaurus", related_name="rel_thesaurus", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.label)

    class Meta:
        ordering = ("lang",)
        verbose_name_plural = "Thesaurus Labels"
        unique_together = (("thesaurus", "lang"),)


class ResourceBaseManager(PolymorphicManager):
    def admin_contact(self):
        # this assumes there is at least one superuser
        superusers = get_user_model().objects.filter(is_superuser=True).order_by("id")
        if superusers.count() == 0:
            raise RuntimeError("GeoNode needs at least one admin/superuser set")

        return superusers[0]

    def get_queryset(self):
        return super().get_queryset().non_polymorphic()

    def polymorphic_queryset(self):
        return super().get_queryset()

    @staticmethod
    def upload_files(resource_id, files, force=False):
        """Update the ResourceBase model"""
        try:
            out = []
            for f in files:
                if force:
                    out.append(f)
                elif os.path.isfile(f) and os.path.exists(f):
                    with open(f, "rb") as ff:
                        folder = os.path.basename(os.path.dirname(f))
                        filename = os.path.basename(f)
                        file_uploaded_path = storage_manager.save(f"{folder}/{filename}", ff)
                        out.append(storage_manager.path(file_uploaded_path))

            # making an update instead of save in order to avoid others
            # signal like post_save and commiunication with geoserver
            ResourceBase.objects.filter(id=resource_id).update(files=out)
            return out
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def cleanup_uploaded_files(resource_id):
        """Remove uploaded files, if any"""
        from geonode.assets.utils import get_default_asset

        if ResourceBase.objects.filter(id=resource_id).exists():
            _resource = ResourceBase.objects.filter(id=resource_id).get()
            asset = get_default_asset(_resource)  # TODO: make sure to select the proper "uploaded" asset
            if asset:
                asset.delete()

            # Remove generated thumbnails, if any
            filename = f"{_resource.get_real_instance().resource_type}-{_resource.get_real_instance().uuid}"
            remove_thumbs(filename)

            # Remove the uploaded sessions, if any
            if "geonode.upload" in settings.INSTALLED_APPS:
                from geonode.upload.models import Upload

                # Need to call delete one by one in order to invoke the
                #  'delete' overridden method
                for upload in Upload.objects.filter(resource_id=_resource.get_real_instance().id):
                    upload.delete()


class ResourceBase(PolymorphicModel, PermissionLevelMixin, ItemBase):
    """
    Base Resource Object loosely based on ISO 19115:2003
    """

    BASE_PERMISSIONS = {
        "read": ["view_resourcebase"],
        "write": ["change_resourcebase_metadata"],
        "download": ["download_resourcebase"],
        "owner": [
            "change_resourcebase",
            "delete_resourcebase",
            "change_resourcebase_permissions",
            "publish_resourcebase",
        ],
    }

    PERMISSIONS = {}

    VALID_DATE_TYPES = [(x.lower(), _(x)) for x in ["Creation", "Publication", "Revision"]]

    abstract_help_text = _("brief narrative summary of the content of the resource(s)")
    date_help_text = _("reference date for the cited resource")
    date_type_help_text = _("identification of when a given event occurred")
    edition_help_text = _("version of the cited resource")
    attribution_help_text = _(
        "authority or function assigned, as to a ruler, legislative assembly, delegate, or the like."
    )
    doi_help_text = _("a DOI will be added by Admin before publication.")
    purpose_help_text = _("summary of the intentions with which the resource(s) was developed")
    maintenance_frequency_help_text = _(
        "frequency with which modifications and deletions are made to the data after " "it is first produced"
    )
    keywords_help_text = _(
        "commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject "
        "(space or comma-separated)"
    )
    tkeywords_help_text = _(
        "formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject "
        "(space or comma-separated)"
    )
    regions_help_text = _("keyword identifies a location")
    restriction_code_type_help_text = _("limitation(s) placed upon the access or use of the data.")
    constraints_other_help_text = _(
        "other restrictions and legal prerequisites for accessing and using the resource or" " metadata"
    )
    license_help_text = _("license of the dataset")
    language_help_text = _("language used within the dataset")
    category_help_text = _(
        "high-level geographic data thematic classification to assist in the grouping and search of "
        "available geographic data sets."
    )
    spatial_representation_type_help_text = _("method used to represent geographic information in the dataset.")
    temporal_extent_start_help_text = _("time period covered by the content of the dataset (start)")
    temporal_extent_end_help_text = _("time period covered by the content of the dataset (end)")
    data_quality_statement_help_text = _(
        "general explanation of the data producer's knowledge about the lineage of a" " dataset"
    )
    extra_metadata_help_text = _(
        'Additional metadata, must be in format [ {"metadata_key": "metadata_value"}, {"metadata_key": "metadata_value"} ]'
    )
    # internal fields
    uuid = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    title = models.CharField(_("title"), max_length=255, help_text=_("name by which the cited resource is known"))
    abstract = models.TextField(_("abstract"), max_length=2000, blank=True, help_text=abstract_help_text)
    purpose = models.TextField(_("purpose"), max_length=500, null=True, blank=True, help_text=purpose_help_text)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="owned_resource", verbose_name=_("Owner"), on_delete=models.PROTECT
    )
    contacts = models.ManyToManyField(settings.AUTH_USER_MODEL, through="ContactRole")
    alternate = models.CharField(_("alternate"), max_length=255, null=True, blank=True)
    date = models.DateTimeField(_("date"), default=now, help_text=date_help_text)
    date_type = models.CharField(
        _("date type"), max_length=255, choices=VALID_DATE_TYPES, default="publication", help_text=date_type_help_text
    )
    edition = models.CharField(_("edition"), max_length=255, blank=True, null=True, help_text=edition_help_text)
    attribution = models.CharField(
        _("Attribution"), max_length=2048, blank=True, null=True, help_text=attribution_help_text
    )
    doi = models.CharField(_("DOI"), max_length=255, blank=True, null=True, help_text=doi_help_text)
    maintenance_frequency = models.CharField(
        _("maintenance frequency"),
        max_length=255,
        choices=enumerations.UPDATE_FREQUENCIES,
        blank=True,
        null=True,
        help_text=maintenance_frequency_help_text,
    )
    keywords = TaggableManager(
        _("keywords"),
        through=TaggedContentItem,
        blank=True,
        help_text=keywords_help_text,
        manager=_HierarchicalTagManager,
    )
    tkeywords = models.ManyToManyField(
        ThesaurusKeyword, verbose_name=_("keywords"), null=True, blank=True, help_text=tkeywords_help_text
    )
    regions = models.ManyToManyField(
        Region, verbose_name=_("keywords region"), null=True, blank=True, help_text=regions_help_text
    )
    restriction_code_type = models.ForeignKey(
        RestrictionCodeType,
        verbose_name=_("restrictions"),
        help_text=restriction_code_type_help_text,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_choice=True),
    )
    constraints_other = models.TextField(
        _("restrictions other"), blank=True, null=True, help_text=constraints_other_help_text
    )
    license = models.ForeignKey(
        License,
        null=True,
        blank=True,
        verbose_name=_("License"),
        help_text=license_help_text,
        on_delete=models.SET_NULL,
    )
    language = models.CharField(
        _("language"), max_length=3, choices=enumerations.ALL_LANGUAGES, default="eng", help_text=language_help_text
    )
    category = models.ForeignKey(
        TopicCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_choice=True),
        help_text=category_help_text,
    )
    spatial_representation_type = models.ForeignKey(
        SpatialRepresentationType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to=Q(is_choice=True),
        verbose_name=_("spatial representation type"),
        help_text=spatial_representation_type_help_text,
    )

    # Section 5
    temporal_extent_start = models.DateTimeField(
        _("temporal extent start"), blank=True, null=True, help_text=temporal_extent_start_help_text
    )
    temporal_extent_end = models.DateTimeField(
        _("temporal extent end"), blank=True, null=True, help_text=temporal_extent_end_help_text
    )
    supplemental_information = models.TextField(
        _("supplemental information"),
        max_length=2000,
        default=enumerations.DEFAULT_SUPPLEMENTAL_INFORMATION,
        help_text=_("any other descriptive information about the dataset"),
    )

    # Section 8
    data_quality_statement = models.TextField(
        _("data quality statement"), max_length=2000, blank=True, null=True, help_text=data_quality_statement_help_text
    )
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)

    # Section 9
    # see metadata_author property definition below

    # Save bbox values in the database.
    # This is useful for spatial searches and for generating thumbnail images
    # and metadata records.
    bbox_polygon = PolygonField(null=True, blank=True)
    ll_bbox_polygon = PolygonField(null=True, blank=True)

    srid = models.CharField(max_length=30, blank=False, null=False, default="EPSG:4326")

    # CSW specific fields
    csw_typename = models.CharField(_("CSW typename"), max_length=32, default="gmd:MD_Metadata", null=False)
    csw_schema = models.CharField(
        _("CSW schema"), max_length=64, default="http://www.isotc211.org/2005/gmd", null=False
    )
    csw_mdsource = models.CharField(_("CSW source"), max_length=256, default="local", null=False)
    csw_insert_date = models.DateTimeField(_("CSW insert date"), auto_now_add=True, null=True)
    csw_type = models.CharField(
        _("CSW type"), max_length=32, default="dataset", null=False, choices=enumerations.HIERARCHY_LEVELS
    )
    csw_anytext = models.TextField(_("CSW anytext"), null=True, blank=True)
    csw_wkt_geometry = models.TextField(
        _("CSW WKT geometry"), null=False, default="POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))"
    )

    # metadata XML specific fields
    metadata_uploaded = models.BooleanField(default=False)
    metadata_uploaded_preserve = models.BooleanField(_("Metadata uploaded preserve"), default=False)
    metadata_xml = models.TextField(
        null=True, default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>', blank=True
    )
    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    featured = models.BooleanField(
        _("Featured"), default=False, help_text=_("Should this resource be advertised in home page?")
    )
    was_published = models.BooleanField(_("Was Published"), default=True, help_text=_("Previous Published state."))
    is_published = models.BooleanField(
        _("Is Published"), default=True, help_text=_("Should this resource be published and searchable?")
    )
    was_approved = models.BooleanField(_("Was Approved"), default=True, help_text=_("Previous Approved state."))
    is_approved = models.BooleanField(
        _("Approved"), default=True, help_text=_("Is this resource validated from a publisher or editor?")
    )
    advertised = models.BooleanField(
        _("Advertised"),
        default=True,
        help_text=_("If False, will hide the resource from search results and catalog listings"),
    )
    # fields necessary for the apis
    thumbnail_url = models.TextField(_("Thumbnail url"), null=True, blank=True)
    thumbnail_path = models.TextField(_("Thumbnail path"), null=True, blank=True)
    rating = models.IntegerField(default=0, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    state = models.CharField(
        _("State"),
        max_length=16,
        null=False,
        blank=False,
        default=enumerations.STATE_READY,
        choices=enumerations.PROCESSING_STATES,
        help_text=_("Hold the resource processing state."),
    )

    sourcetype = models.CharField(
        _("Source Type"),
        max_length=16,
        null=False,
        blank=False,
        default=enumerations.SOURCE_TYPE_LOCAL,
        choices=enumerations.SOURCE_TYPES,
        help_text=_('The resource source type, which can be one of "LOCAL", "REMOTE" or "COPYREMOTE".'),
    )

    remote_typename = models.CharField(
        _("Remote Service Typename"),
        null=True,
        blank=True,
        max_length=512,
        help_text=_("Name of the Remote Service if any."),
    )

    # fields controlling security state
    dirty_state = models.BooleanField(
        _("Dirty State"), default=False, help_text=_("Security Rules Are Not Synched with GeoServer!")
    )

    users_geolimits = models.ManyToManyField("UserGeoLimit", related_name="users_geolimits", null=True, blank=True)

    groups_geolimits = models.ManyToManyField("GroupGeoLimit", related_name="groups_geolimits", null=True, blank=True)

    resource_type = models.CharField(_("Resource Type"), max_length=1024, blank=True, null=True)

    metadata_only = models.BooleanField(
        _("Metadata"), default=False, help_text=_("If true, will be excluded from search")
    )

    blob = JSONField(null=True, default=dict, blank=True)

    subtype = models.CharField(max_length=128, null=True, blank=True)

    metadata = models.ManyToManyField(
        "ExtraMetadata", verbose_name=_("Extra Metadata"), null=True, blank=True, help_text=extra_metadata_help_text
    )

    objects = ResourceBaseManager()

    class Meta:
        # custom permissions,
        # add, change and delete are standard in django-guardian
        permissions = (
            # ('view_resourcebase', 'Can view resource'),
            ("change_resourcebase_permissions", "Can change resource permissions"),
            ("download_resourcebase", "Can download resource"),
            ("publish_resourcebase", "Can publish resource"),
            ("change_resourcebase_metadata", "Can change resource metadata"),
        )

    def __init__(self, *args, **kwargs):
        # Provide legacy support for bbox fields
        try:
            bbox = [kwargs.pop(key, None) for key in ("bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1")]
            if all(bbox):
                kwargs["bbox_polygon"] = Polygon.from_bbox(bbox)
                kwargs["ll_bbox_polygon"] = Polygon.from_bbox(bbox)
        except Exception as e:
            logger.exception(e)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return str(self.title)

    def _remove_html_tags(self, attribute_str):
        _attribute_str = attribute_str
        try:
            pattern = re.compile("<.*?>")
            _attribute_str = html.unescape(
                re.sub(pattern, "", attribute_str).replace("\n", " ").replace("\r", "").strip()
            )
        except Exception:
            if attribute_str:
                _attribute_str = html.unescape(attribute_str.replace("\n", " ").replace("\r", "").strip())
        return strip_tags(_attribute_str)

    @classproperty
    def allowed_permissions(cls):
        return {
            "anonymous": VIEW_PERMISSIONS,
            "default": OWNER_PERMISSIONS,
            groups_settings.REGISTERED_MEMBERS_GROUP_NAME: OWNER_PERMISSIONS,
        }

    @classproperty
    def compact_permission_labels(cls):
        return {
            "none": _("None"),
            "view": _("View"),
            "download": _("Download"),
            "edit": _("Edit"),
            "manage": _("Manage"),
            "owner": _("Owner"),
        }

    @property
    def raw_abstract(self):
        return self._remove_html_tags(self.abstract)

    @property
    def raw_purpose(self):
        return self._remove_html_tags(self.purpose)

    @property
    def raw_constraints_other(self):
        return self._remove_html_tags(self.constraints_other)

    @property
    def raw_supplemental_information(self):
        return self._remove_html_tags(self.supplemental_information)

    @property
    def raw_data_quality_statement(self):
        return self._remove_html_tags(self.data_quality_statement)

    @property
    def detail_url(self):
        return self.get_absolute_url()

    def clean(self):
        if self.title:
            self.title = self.title.replace(",", "_")
        return super().clean()

    def save(self, notify=False, *args, **kwargs):
        """
        Send a notification when a resource is created or updated
        """
        if not self.resource_type and self.polymorphic_ctype and self.polymorphic_ctype.model:
            self.resource_type = self.polymorphic_ctype.model.lower()

        # Resource Updated
        _notification_sent = False
        _group_status_changed = False
        _approval_status_changed = False

        if hasattr(self, "class_name") and (self.pk is None or notify):
            if self.pk is None and (self.title or getattr(self, "name", None)):
                # Resource Created
                if not self.title and getattr(self, "name", None):
                    self.title = getattr(self, "name", None)
                notice_type_label = f"{self.class_name.lower()}_created"
                recipients = get_notification_recipients(notice_type_label, resource=self)
                send_notification(recipients, notice_type_label, {"resource": self})
            elif self.pk:
                # Group has changed
                _group_status_changed = self.group != ResourceBase.objects.get(pk=self.get_self_resource().pk).group

                # Approval Notifications Here
                if self.was_approved != self.is_approved:
                    if not _notification_sent and not self.was_approved and self.is_approved:
                        # Send "approved" notification
                        notice_type_label = f"{self.class_name.lower()}_approved"
                        recipients = get_notification_recipients(notice_type_label, resource=self)
                        send_notification(recipients, notice_type_label, {"resource": self})
                        _notification_sent = True
                    self.was_approved = self.is_approved
                    _approval_status_changed = True

                # Publishing Notifications Here
                if self.was_published != self.is_published:
                    if not _notification_sent and not self.was_published and self.is_published:
                        # Send "published" notification
                        notice_type_label = f"{self.class_name.lower()}_published"
                        recipients = get_notification_recipients(notice_type_label, resource=self)
                        send_notification(recipients, notice_type_label, {"resource": self})
                        _notification_sent = True
                    self.was_published = self.is_published
                    _approval_status_changed = True

                # Updated Notifications Here
                if not _notification_sent:
                    notice_type_label = f"{self.class_name.lower()}_updated"
                    recipients = get_notification_recipients(notice_type_label, resource=self)
                    send_notification(recipients, notice_type_label, {"resource": self})

        if self.pk is None:
            _initial_value = ResourceBase.objects.aggregate(Max("pk"))["pk__max"]
            if not _initial_value:
                _initial_value = 1
            else:
                _initial_value += 1
            _next_value = get_next_value("ResourceBase", initial_value=_initial_value)  # type(self).__name__,
            if _initial_value > _next_value:
                Sequence.objects.filter(name="ResourceBase").update(last=_initial_value)
                _next_value = _initial_value

            self.pk = self.id = _next_value

        if isinstance(self.uuid, uuid.UUID):
            self.uuid = str(self.uuid)
        elif not self.uuid or callable(self.uuid) or len(self.uuid) == 0:
            self.uuid = str(uuid.uuid4())
        super().save(*args, **kwargs)

        # Update workflow permissions
        if _approval_status_changed or _group_status_changed:
            self.set_permissions(
                approval_status_changed=_approval_status_changed, group_status_changed=_group_status_changed
            )

    def delete(self, notify=True, *args, **kwargs):
        """
        Send a notification when a layer, map or document is deleted
        """
        from geonode.resource.manager import resource_manager

        resource_manager.remove_permissions(self.uuid, instance=self.get_real_instance())

        # delete assets. TODO: when standalone Assets will be allowed, only dependable Assets shall be removed
        links_with_assets = Link.objects.filter(resource=self, asset__isnull=False).prefetch_related("asset")
        for link in links_with_assets:
            link.asset.delete()

        if hasattr(self, "class_name") and notify:
            notice_type_label = f"{self.class_name.lower()}_deleted"
            recipients = get_notification_recipients(notice_type_label, resource=self)
            send_notification(recipients, notice_type_label, {"resource": self})

        super().delete(*args, **kwargs)

    def get_upload_session(self):
        raise NotImplementedError()

    @property
    def site_url(self):
        return settings.SITEURL

    @property
    def creator(self):
        return self.owner.get_full_name() or self.owner.username

    @property
    def perms(self):
        return []

    @property
    def organizationname(self):
        return self.owner.organization

    @property
    def restriction_code(self):
        return self.restriction_code_type.gn_description if self.restriction_code_type else None

    @property
    def topiccategory(self):
        return self.category.identifier if self.category else None

    @property
    def csw_crs(self):
        return "EPSG:4326"

    @property
    def group_name(self):
        return str(self.group).encode("utf-8", "replace") if self.group else None

    @property
    def bbox(self):
        """BBOX is in the format: [x0, x1, y0, y1, srid]."""
        if self.bbox_polygon:
            match = re.match(r"^(EPSG:)?(?P<srid>\d{4,6})$", self.srid)
            srid = int(match.group("srid")) if match else 4326
            bbox = BBOXHelper(self.bbox_polygon.extent)
            return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, f"EPSG:{srid}"]
        bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
        return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]

    @property
    def ll_bbox(self):
        """BBOX is in the format [x0, x1, y0, y1, "EPSG:srid"]. Provides backwards
        compatibility after transition to polygons."""
        if self.ll_bbox_polygon:
            _bbox = self.ll_bbox_polygon.extent
            srid = self.ll_bbox_polygon.srid
            return [_bbox[0], _bbox[2], _bbox[1], _bbox[3], f"EPSG:{srid}"]
        bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
        return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]

    @property
    def ll_bbox_string(self):
        """WGS84 BBOX is in the format: [x0,y0,x1,y1]."""
        if self.bbox_polygon:
            bbox = BBOXHelper.from_xy(self.ll_bbox[:4])

            return f"{bbox.xmin:.7f},{bbox.ymin:.7f},{bbox.xmax:.7f},{bbox.ymax:.7f}"
        bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
        return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]

    @property
    def bbox_string(self):
        """BBOX is in the format: [x0, y0, x1, y1]. Provides backwards compatibility
        after transition to polygons."""
        if self.bbox_polygon:
            bbox = BBOXHelper.from_xy(self.bbox[:4])

            return f"{bbox.xmin:.7f},{bbox.ymin:.7f},{bbox.xmax:.7f},{bbox.ymax:.7f}"
        bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
        return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]

    @property
    def bbox_helper(self):
        if self.bbox_polygon:
            return BBOXHelper(self.bbox_polygon.extent)
        bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
        return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]

    @cached_property
    def bbox_x0(self):
        if self.bbox_polygon:
            return self.bbox[0]
        return None

    @cached_property
    def bbox_x1(self):
        if self.bbox_polygon:
            return self.bbox[1]
        return None

    @cached_property
    def bbox_y0(self):
        if self.bbox_polygon:
            return self.bbox[2]
        return None

    @cached_property
    def bbox_y1(self):
        if self.bbox_polygon:
            return self.bbox[3]
        return None

    @property
    def geographic_bounding_box(self):
        """
        Returns an EWKT representation of the bounding box in EPSG:4326
        """
        if self.ll_bbox_polygon:
            bbox = polygon_from_bbox(self.ll_bbox_polygon.extent, 4326)
            return str(bbox)
        else:
            bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
            return bbox_to_wkt(bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, srid="EPSG:4326")

    @property
    def license_light(self):
        a = []
        if not self.license:
            return ""
        if self.license.name is not None and (len(self.license.name) > 0):
            a.append(self.license.name)
        if self.license.url is not None and (len(self.license.url) > 0):
            a.append(f"({self.license.url})")
        return " ".join(a)

    @property
    def license_verbose(self):
        a = []
        if self.license.name_long is not None and (len(self.license.name_long) > 0):
            a.append(f"{self.license.name_long}:")
        if self.license.description is not None and (len(self.license.description) > 0):
            a.append(self.license.description)
        if self.license.url is not None and (len(self.license.url) > 0):
            a.append(f"({self.license.url})")
        return " ".join(a)

    @property
    def metadata_completeness(self):
        required_fields = [
            "abstract",
            "category",
            "data_quality_statement",
            "date",
            "date_type",
            "language",
            "license",
            "regions",
            "title",
        ]
        if self.restriction_code_type and self.restriction_code_type.identifier == "otherRestrictions":
            required_fields.append("constraints_other")
        filled_fields = []
        for required_field in required_fields:
            field = getattr(self, required_field, None)
            if field:
                if required_field == "license":
                    if field.name == "Not Specified":
                        continue
                if required_field == "regions":
                    if not field.all():
                        continue
                if required_field == "category":
                    if not field.identifier:
                        continue
                filled_fields.append(field)
        return f"{len(filled_fields) * 100 / len(required_fields)}%"

    @property
    def instance_is_processed(self):
        try:
            if hasattr(self.get_real_instance(), "processed"):
                return self.get_real_instance().processed
            return False
        except Exception:
            return False

    @property
    def is_copyable(self):
        if self.resource_type == "dataset":
            from geonode.assets.utils import get_default_asset
            from geonode.geoserver.helpers import select_relevant_files

            asset = get_default_asset(self)  # TODO: maybe we need to filter by original files
            allowed_file = select_relevant_files(get_allowed_extensions(), asset.location) if asset else []
            return len(allowed_file) != 0
        return True

    def keyword_list(self):
        return [kw.name for kw in self.keywords.all()]

    def keyword_slug_list(self):
        return [kw.slug for kw in self.keywords.all()]

    def region_name_list(self):
        return [region.name for region in self.regions.all()]

    def spatial_representation_type_string(self):
        if hasattr(self.spatial_representation_type, "identifier"):
            return self.spatial_representation_type.identifier
        else:
            if hasattr(self, "subtype"):
                if self.subtype == "raster":
                    return "grid"
                return "vector"
            else:
                return None

    def set_dirty_state(self):
        if not self.dirty_state:
            self.dirty_state = True
            ResourceBase.objects.filter(id=self.id).update(dirty_state=True)

    def clear_dirty_state(self):
        if self.dirty_state:
            self.dirty_state = False
            ResourceBase.objects.filter(id=self.id).update(dirty_state=False)

    def set_processing_state(self, state):
        self.state = state
        ResourceBase.objects.filter(id=self.id).update(state=state)
        if state == enumerations.STATE_PROCESSED:
            self.clear_dirty_state()
        elif state == enumerations.STATE_INVALID:
            self.set_dirty_state()

    @property
    def processed(self):
        return self.state == enumerations.STATE_PROCESSED and not self.dirty_state

    @property
    def keyword_csv(self):
        try:
            keywords_qs = self.get_real_instance().keywords.all()
            if keywords_qs:
                return ",".join(kw.name for kw in keywords_qs)
            else:
                return ""
        except Exception:
            return ""

    def get_absolute_url(self):
        from geonode.client.hooks import hookset

        try:
            return (
                self.get_real_instance().get_absolute_url()
                if self != self.get_real_instance()
                else hookset.get_absolute_url(self)
            )
        except Exception as e:
            logger.exception(e)
            return None

    def set_bbox_polygon(self, bbox, srid):
        """
        Set `bbox_polygon` from bbox values.

        :param bbox: list or tuple formatted as
            [xmin, ymin, xmax, ymax]
        :param srid: srid as string (e.g. 'EPSG:4326' or '4326')
        """
        try:
            bbox_polygon = Polygon.from_bbox(bbox)
            self.bbox_polygon = bbox_polygon.clone()
            self.srid = srid
            # This is a trick in order to avoid PostGIS reprojecting the bbox at save time
            # by assuming the default geometries have 'EPSG:4326' as srid.
            ResourceBase.objects.filter(id=self.id).update(bbox_polygon=self.bbox_polygon, srid=srid)
        finally:
            self.set_ll_bbox_polygon(bbox, srid=srid)

    def set_ll_bbox_polygon(self, bbox, srid="EPSG:4326"):
        """
        Set `ll_bbox_polygon` from bbox values.

        :param bbox: list or tuple formatted as
            [xmin, ymin, xmax, ymax]
        :param srid: srid as string (e.g. 'EPSG:4326' or '4326')
        """
        try:
            bbox_polygon = Polygon.from_bbox(bbox)
            if srid == 4326 or srid.upper() == "EPSG:4326":
                self.ll_bbox_polygon = bbox_polygon
            else:
                match = re.match(r"^(EPSG:)?(?P<srid>\d{4,6})$", str(srid))
                bbox_polygon.srid = int(match.group("srid")) if match else 4326

                # Adapt coords order from xmin,ymin,xmax,ymax to xmin,xmax,ymin,ymax
                standard_extent = list(bbox_polygon.extent)
                bbox_gn_order = bbox_swap(standard_extent) + [srid]
                projected_bbox_gn_order = bbox_to_projection(bbox_gn_order)
                projected_bbox = bbox_swap(projected_bbox_gn_order[:-1])

                self.ll_bbox_polygon = Polygon.from_bbox(projected_bbox)
            ResourceBase.objects.filter(id=self.id).update(ll_bbox_polygon=self.ll_bbox_polygon)
        except Exception as e:
            raise GeoNodeException(e)

    def set_bounds_from_bbox(self, bbox, srid):
        """
        Calculate zoom level and center coordinates in mercator.

        :param bbox: BBOX is either a `geos.Pologyon` or in the
            format: [x0, x1, y0, y1], which is:
            [min lon, max lon, min lat, max lat] or
            [xmin, xmax, ymin, ymax]
        :type bbox: list
        """
        if isinstance(bbox, Polygon):
            self.set_bbox_polygon(bbox.extent, srid)
            self.set_center_zoom()
            return
        elif isinstance(bbox, list):
            self.set_bbox_polygon([bbox[0], bbox[2], bbox[1], bbox[3]], srid)
            self.set_center_zoom()
            return

        if not bbox or len(bbox) < 4:
            raise ValidationError(f"Bounding Box cannot be empty {self.name} for a given resource")
        if not srid:
            raise ValidationError(f"Projection cannot be empty {self.name} for a given resource")

        self.srid = srid
        self.set_bbox_polygon((bbox[0], bbox[2], bbox[1], bbox[3]), srid)
        self.set_center_zoom()

    def set_center_zoom(self):
        """
        Sets the center coordinates and zoom level in EPSG:4326
        """
        if self.ll_bbox_polygon and len(self.ll_bbox_polygon.centroid.coords) > 0:
            bbox = self.ll_bbox_polygon.clone()
            center_x, center_y = bbox.centroid.coords
            center = Point(center_x, center_y, srid=4326)
            self.center_x, self.center_y = center.coords
            try:
                ext = bbox.extent
                width_zoom = math.log(360 / (ext[2] - ext[0]), 2)
                height_zoom = math.log(360 / (ext[3] - ext[1]), 2)
                self.zoom = math.ceil(min(width_zoom, height_zoom))
            except ZeroDivisionError:
                pass

    def download_links(self):
        """assemble download links for pycsw"""
        links = []
        for link in self.link_set.all():
            if link.link_type == "metadata":  # avoid recursion
                continue
            if link.link_type == "html":
                links.append((self.title, "Web address (URL)", "WWW:LINK-1.0-http--link", link.url))
            elif link.link_type in ("OGC:WMS", "OGC:WFS", "OGC:WCS"):
                links.append((self.title, link.name, link.link_type, link.url))
            else:
                _link_type = "WWW:DOWNLOAD-1.0-http--download"
                try:
                    _store_type = getattr(self.get_real_instance(), "subtype", None)
                    if _store_type and _store_type in ["tileStore", "remote"] and link.extension in ("html"):
                        _remote_service = getattr(self.get_real_instance(), "_remote_service", None)
                        if _remote_service:
                            _link_type = f"WWW:DOWNLOAD-{_remote_service.type}"
                except Exception as e:
                    logger.exception(e)
                description = f"{self.title} ({link.name} Format)"
                links.append((self.title, description, _link_type, link.url))
        return links

    @property
    def embed_url(self):
        return (
            self.get_real_instance().embed_url
            if self != self.get_real_instance()
            else reverse("resourcebase_embed", kwargs={"resourcebaseid": self.pk})
        )

    def get_tiles_url(self):
        """Return URL for Z/Y/X mapping clients or None if it does not exist."""
        try:
            tiles_link = self.link_set.get(name="Tiles")
        except Link.DoesNotExist:
            return None
        else:
            return tiles_link.url

    def get_legend(self):
        """Return Link for legend or None if it does not exist."""
        try:
            legends_link = self.link_set.filter(name="Legend")
        except Link.DoesNotExist:
            tb = traceback.format_exc()
            logger.debug(tb)
            return None
        except Link.MultipleObjectsReturned:
            tb = traceback.format_exc()
            logger.debug(tb)
            return None
        else:
            return legends_link

    def get_legend_url(self, style_name=None):
        """Return URL for legend or None if it does not exist.

        The legend can be either an image (for Geoserver's WMS)
        or a JSON object for ArcGIS.
        """
        legend = self.get_legend()

        if legend is None:
            return None

        if legend.exists():
            if not style_name:
                return legend.first().url
            else:
                for _legend in legend:
                    if style_name in _legend.url:
                        return _legend.url
        return None

    def get_ows_url(self):
        """Return URL for OGC WMS server None if it does not exist."""
        try:
            ows_link = self.link_set.get(name="OGC:WMS")
        except Link.DoesNotExist:
            return None
        else:
            return ows_link.url

    def get_thumbnail_url(self):
        """Return a thumbnail url.

        It could be a local one if it exists, a remote one (WMS GetImage) for example
        """
        _thumbnail_url = self.thumbnail_url
        local_thumbnails = self.link_set.filter(name="Thumbnail")
        remote_thumbnails = self.link_set.filter(name="Remote Thumbnail")
        if local_thumbnails.exists():
            _thumbnail_url = local_thumbnails.first().url
        elif remote_thumbnails.exists():
            _thumbnail_url = remote_thumbnails.first().url
        return _thumbnail_url

    def has_thumbnail(self):
        """Determine if the thumbnail object exists and an image exists"""
        return self.link_set.filter(name="Thumbnail").exists()

    # Note - you should probably broadcast layer#post_save() events to ensure
    # that indexing (or other listeners) are notified
    def save_thumbnail(self, filename, image, thumbnail_algorithm=ThumbnailAlgorithms.fit, **kwargs):
        upload_path = get_unique_upload_path(filename)
        # force conversion to JPEG output file
        upload_path = f"{os.path.splitext(upload_path)[0]}.jpg"
        try:
            # Check that the image is valid
            if is_monochromatic_image(None, image):
                if not self.thumbnail_url and not image:
                    raise Exception("Generated thumbnail image is blank")
                else:
                    # Skip Image creation
                    image = None

            if image:
                actual_name = storage_manager.save(upload_path, ContentFile(image))
                actual_file_name = os.path.basename(actual_name)

                if filename != actual_file_name:
                    upload_path = upload_path.replace(filename, actual_file_name)
                url = storage_manager.url(upload_path)
                try:
                    # Optimize the Thumbnail size and resolution
                    im = Image.open(storage_manager.open(actual_name))
                    im = thumbnail_algorithm(im, **kwargs)

                    # Saving the thumb into a temporary directory on file system
                    tmp_location = os.path.abspath(f"{settings.MEDIA_ROOT}/{upload_path}")
                    im.save(tmp_location, quality="high")

                    with open(tmp_location, "rb+") as img:
                        # Saving the img via storage manager
                        storage_manager.save(upload_path, img)

                    # If we use a remote storage, the local img is deleted
                    if tmp_location != storage_manager.path(upload_path):
                        os.remove(tmp_location)
                except Exception as e:
                    logger.exception(e)

                # check whether it is an URI or not
                parsed = urlsplit(url)
                if not parsed.netloc:
                    # assuming is a relative path to current site
                    site_url = settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL
                    url = urljoin(site_url, url)

                if thumb_size(upload_path) == 0:
                    raise Exception("Generated thumbnail image is zero size")

                # should only have one 'Thumbnail' link
                Link.objects.filter(resource=self, name="Thumbnail").delete()
                obj, _created = Link.objects.get_or_create(
                    resource=self,
                    name="Thumbnail",
                    defaults=dict(
                        url=url,
                        extension="png",
                        mime="image/png",
                        link_type="image",
                    ),
                )
                # Cleaning up the old stuff
                if self.thumbnail_path and storage_manager.exists(self.thumbnail_path):
                    storage_manager.delete(self.thumbnail_path)
                # Store the new url and path
                self.thumbnail_url = url
                self.thumbnail_path = upload_path
                obj.url = url
                obj.save()
                ResourceBase.objects.filter(id=self.id).update(thumbnail_url=url, thumbnail_path=upload_path)
        except Exception as e:
            logger.error(f"Error when generating the thumbnail for resource {self.id}. ({e})")
            try:
                Link.objects.filter(resource=self, name="Thumbnail").delete()
            except Exception as e:
                logger.error(f"Error when generating the thumbnail for resource {self.id}. ({e})")

    def set_missing_info(self):
        """Set default permissions and point of contacts.

        It is mandatory to call it from descendant classes
        but hard to enforce technically via signals or save overriding.
        """
        user = None
        if self.owner:
            user = self.owner
        else:
            try:
                user = ResourceBase.objects.admin_contact().user
            except Exception:
                pass

        if user:
            if len(self.poc) == 0:
                self.poc = [user]
            if len(self.metadata_author) == 0:
                self.metadata_author = [user]

        from guardian.models import UserObjectPermission

        logger.debug("Checking for permissions.")
        #  True if every key in the get_all_level_info dict is empty.
        no_custom_permissions = UserObjectPermission.objects.filter(
            content_type=ContentType.objects.get_for_model(self.get_self_resource()), object_pk=str(self.pk)
        ).exists()

        if not no_custom_permissions:
            logger.debug("There are no permissions for this object, setting default perms.")
            self.set_default_permissions(owner=user)

    def maintenance_frequency_title(self):
        return [v for v in enumerations.UPDATE_FREQUENCIES if v[0] == self.maintenance_frequency][0][1].title()

    def language_title(self):
        return [v for v in enumerations.ALL_LANGUAGES if v[0] == self.language][0][1].title()

    # Contact Roles
    def add_missing_metadata_author_or_poc(self):
        """
        Set metadata_author and/or point of contact (poc) to a resource when any of them is missing
        """
        if len(self.metadata_author) == 0:
            self.metadata_author = [self.owner]
        if len(self.poc) == 0:
            self.poc = [self.owner]

    @staticmethod
    def get_multivalue_role_property_names() -> List[str]:
        """returns list of property names for all contact roles able to
            handle multiple profile_users

        Returns:
            _type_: List(str)
            _description: list of names
        """
        return [role.name for role in Roles.get_multivalue_ones()]

    @staticmethod
    def get_multivalue_required_role_property_names() -> List[str]:
        """returns list of property names for all contact roles that are required

        Returns:
            _type_: List(str)
            _description: list of names
        """
        return [role.name for role in (set(Roles.get_multivalue_ones()) & set(Roles.get_required_ones()))]

    @staticmethod
    def get_ui_toggled_role_property_names() -> List[str]:
        """returns list of property names for all contact roles that are toggled of in metadata_editor

        Returns:
            _type_: List(str)
            _description: list of names
        """
        return [role.name for role in (set(Roles.get_toggled_ones()) & set(Roles.get_toggled_ones()))]

    # typing not possible due to: from geonode.base.forms import ResourceBaseForm; unable due to circular ...
    def set_contact_roles_from_metadata_edit(self, resource_base_form) -> bool:
        """gets a ResourceBaseForm and extracts the Contact Role elements from it

        Args:
            resource_base_form (ResourceBaseForm): ResourceBaseForm with contact roles set

        Returns:
            bool: true if all contact roles could be set, else false
        """
        failed = False
        for role in self.get_multivalue_role_property_names():
            try:
                self.__setattr__(role, resource_base_form.cleaned_data[role])
            except AttributeError:
                logger.warning(f"unable to set contact role {role} for {self} ...")
                failed = True
        return failed

    def __get_contact_role_elements__(self, role: str) -> Optional[List[settings.AUTH_USER_MODEL]]:
        """general getter of for all contact roles except owner

        Args:
            role (str): string coresponding to ROLE_VALUES in geonode/people/enumarations, defining which propery is requested
        Returns:
            Optional[List[settings.AUTH_USER_MODEL]]: returns the requested contact role from the database
        """
        try:
            contact_role = ContactRole.objects.filter(role=role, resource=self)
            contacts = [cr.contact for cr in contact_role]
        except ContactRole.DoesNotExist:
            contacts = None
        return contacts

    # types allowed as input for Contact role properties
    CONTACT_ROLE_USER_PROFILES_ALLOWED_TYPES = Union[settings.AUTH_USER_MODEL, QuerySet, List[settings.AUTH_USER_MODEL]]

    def __set_contact_role_element__(self, user_profile: CONTACT_ROLE_USER_PROFILES_ALLOWED_TYPES, role: str):
        """general setter for all contact roles except owner in resource base

        Args:
            user_profile (CONTACT_ROLE_USER_PROFILES_ALLOWED_TYPES): _description_
            role (str): tring coresponding to ROLE_VALUES in geonode/people/enumarations, defining which propery is to set
        """

        def __create_role__(
            resource, role: str, user_profile: settings.AUTH_USER_MODEL
        ) -> List[settings.AUTH_USER_MODEL]:
            return ContactRole.objects.create(role=role, resource=resource, contact=user_profile)

        if isinstance(user_profile, QuerySet):
            ContactRole.objects.filter(role=role, resource=self).delete()
            return [__create_role__(self, role, user) for user in user_profile]

        elif isinstance(user_profile, get_user_model()):
            ContactRole.objects.filter(role=role, resource=self).delete()
            return __create_role__(self, role, user_profile)

        elif isinstance(user_profile, list) and all(
            get_user_model().objects.filter(username=x).exists() for x in user_profile
        ):
            ContactRole.objects.filter(role=role, resource=self).delete()
            return [
                __create_role__(self, role, user) for user in get_user_model().objects.filter(username__in=user_profile)
            ]

        elif user_profile is None:
            ContactRole.objects.filter(role=role, resource=self).delete()
        else:
            logger.error(f"Bad profile format for role: {role} ...")

    def get_defined_multivalue_contact_roles(self) -> List[Tuple[List[settings.AUTH_USER_MODEL], str]]:
        """Returns all set contact roles of the ressource with additional ROLE_VALUES from geonode.people.enumarations.ROLE_VALUES. Mainly used to generate output xml more easy.

        Returns:
              _type_: List[Tuple[List[people object], roles_label_name]]
              _description: list tuples including two elements: 1. list of people have a certain role. 2. role label
        """
        return {
            role.label: self.__getattribute__(role.name)
            for role in Roles.get_multivalue_ones()
            if self.__getattribute__(role.name)
        }

    def get_first_contact_of_role(self, role: str) -> Optional[ContactRole]:
        """
        Get the first contact from the specified role.

        Parameters:
            role (str): The role of the contact.

        Returns:
            ContactRole or None: The first contact with the specified role, or None if not found.
        """
        if contact := self.__get_contact_role_elements__(role):
            return contact[0]
        else:
            return None

    # Contact Role: POC (pointOfContact)
    def __get_poc__(self) -> List[settings.AUTH_USER_MODEL]:
        return self.__get_contact_role_elements__(role="pointOfContact")

    def __set_poc__(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role="pointOfContact")

    poc = property(__get_poc__, __set_poc__)

    @property
    def poc_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.poc)

    # Contact Role: metadata_author
    def _get_metadata_author(self):
        return self.__get_contact_role_elements__(role="author")

    def _set_metadata_author(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role="author")

    metadata_author = property(_get_metadata_author, _set_metadata_author)

    @property
    def metadata_author_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.metadata_author)

    # Contact Role: PROCESSOR
    def _get_processor(self):
        return self.__get_contact_role_elements__(role=Roles.PROCESSOR.name)

    def _set_processor(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.PROCESSOR.name)

    processor = property(_get_processor, _set_processor)

    @property
    def processor_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.processor)

    # Contact Role: PUBLISHER
    def _get_publisher(self):
        return self.__get_contact_role_elements__(role=Roles.PUBLISHER.name)

    def _set_publisher(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.PUBLISHER.name)

    publisher = property(_get_publisher, _set_publisher)

    @property
    def publisher_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.publisher)

    # Contact Role: CUSTODIAN
    def _get_custodian(self):
        return self.__get_contact_role_elements__(role=Roles.CUSTODIAN.name)

    def _set_custodian(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.CUSTODIAN.name)

    custodian = property(_get_custodian, _set_custodian)

    @property
    def custodian_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.custodian)

    # Contact Role: DISTRIBUTOR
    def _get_distributor(self):
        return self.__get_contact_role_elements__(role=Roles.DISTRIBUTOR.name)

    def _set_distributor(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.DISTRIBUTOR.name)

    distributor = property(_get_distributor, _set_distributor)

    @property
    def distributor_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.distributor)

    # Contact Role: RESOURCE_USER
    def _get_resource_user(self):
        return self.__get_contact_role_elements__(role=Roles.RESOURCE_USER.name)

    def _set_resource_user(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.RESOURCE_USER.name)

    resource_user = property(_get_resource_user, _set_resource_user)

    @property
    def resource_user_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.resource_user)

    # Contact Role: RESOURCE_PROVIDER
    def _get_resource_provider(self):
        return self.__get_contact_role_elements__(role=Roles.RESOURCE_PROVIDER.name)

    def _set_resource_provider(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.RESOURCE_PROVIDER.name)

    resource_provider = property(_get_resource_provider, _set_resource_provider)

    @property
    def resource_provider_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.resource_provider)

    # Contact Role: ORIGINATOR
    def _get_originator(self):
        return self.__get_contact_role_elements__(role=Roles.ORIGINATOR.name)

    def _set_originator(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.ORIGINATOR.name)

    originator = property(_get_originator, _set_originator)

    @property
    def originator_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.originator)

    # Contact Role: PRINCIPAL_INVESTIGATOR
    def _get_principal_investigator(self):
        return self.__get_contact_role_elements__(role=Roles.PRINCIPAL_INVESTIGATOR.name)

    def _set_principal_investigator(self, user_profile):
        return self.__set_contact_role_element__(user_profile=user_profile, role=Roles.PRINCIPAL_INVESTIGATOR.name)

    principal_investigator = property(_get_principal_investigator, _set_principal_investigator)

    @property
    def principal_investigator_csv(self):
        return ",".join(p.get_full_name() or p.username for p in self.principal_investigator)

    def get_linked_resources(self, as_target: bool = False):
        """
        Get all the linked resources to this ResourceBase instance.
        This is implemented as a method so that derived classes can override it (for instance, Maps may add
        related datasets)
        """
        return (
            LinkedResource.get_linked_resources(target=self)
            if as_target
            else LinkedResource.get_linked_resources(source=self)
        )


class LinkManager(models.Manager):
    """Helper class to access links grouped by type"""

    def data(self):
        return self.get_queryset().filter(link_type="data")

    def image(self):
        return self.get_queryset().filter(link_type="image")

    def download(self):
        return self.get_queryset().filter(link_type__in=["image", "data", "original"])

    def metadata(self):
        return self.get_queryset().filter(link_type="metadata")

    def original(self):
        return self.get_queryset().filter(link_type="original")

    def ows(self):
        return self.get_queryset().filter(link_type__in=["OGC:WMS", "OGC:WFS", "OGC:WCS"])


class LinkedResource(models.Model):
    source = models.ForeignKey(
        ResourceBase, related_name="linked_to", blank=False, null=False, on_delete=models.CASCADE
    )
    target = models.ForeignKey(ResourceBase, related_name="linked_by", blank=True, null=False, on_delete=models.CASCADE)
    internal = models.BooleanField(null=False, default=False)

    @classmethod
    def get_linked_resources(cls, source: ResourceBase = None, target: ResourceBase = None, is_internal: bool = None):
        if source is None and target is None:
            raise ValueError("Both source and target filters missing")

        qs = LinkedResource.objects
        if source:
            qs = qs.filter(source=source).select_related("target")
        if target:
            qs = qs.filter(target=target).select_related("source")
        if is_internal is not None:
            qs = qs.filter(internal=is_internal)
        return qs

    @classmethod
    def get_target_ids(cls, source: ResourceBase, is_internal: bool = None):
        sub = LinkedResource.objects.filter(source=source).values_list("target_id", flat=True)
        if is_internal is not None:
            sub = sub.filter(internal=is_internal)
        return sub

    @classmethod
    def get_targets(cls, source: ResourceBase, is_internal: bool = None):
        return ResourceBase.objects.filter(id__in=cls.get_target_ids(source, is_internal))

    @classmethod
    def resolve_targets(cls, linked_resources):
        return (lr.target for lr in linked_resources)

    @classmethod
    def resolve_sources(cls, linked_resources):
        return (lr.source for lr in linked_resources)


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

    resource = models.ForeignKey(ResourceBase, blank=True, null=True, on_delete=models.CASCADE)
    extension = models.CharField(max_length=255, help_text=_('For example "kml"'))
    link_type = models.CharField(max_length=255, choices=[(x, x) for x in enumerations.LINK_TYPES])
    name = models.CharField(max_length=255, help_text=_('For example "View in Google Earth"'))
    mime = models.CharField(max_length=255, help_text=_('For example "text/xml"'))
    url = models.TextField(max_length=1000)
    asset = models.ForeignKey("assets.Asset", null=True, on_delete=models.CASCADE)

    objects = LinkManager()

    def __str__(self):
        return f"{self.link_type} link"


class MenuPlaceholder(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def __str__(self):
        return str(self.name)


class Menu(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    placeholder = models.ForeignKey(to="MenuPlaceholder", on_delete=models.CASCADE, null=False)
    order = models.IntegerField(
        null=False,
    )

    def __str__(self):
        return str(self.title)

    class Meta:
        unique_together = (
            ("placeholder", "order"),
            ("placeholder", "title"),
        )
        ordering = ["order"]


class MenuItem(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    menu = models.ForeignKey(to="Menu", null=False, on_delete=models.CASCADE)
    order = models.IntegerField(null=False)
    blank_target = models.BooleanField()
    url = models.CharField(max_length=2000, null=False, blank=False)

    def __eq__(self, other):
        return self.order == other.order

    def __ne__(self, other):
        return self.order != other.order

    def __lt__(self, other):
        return self.order < other.order

    def __le__(self, other):
        return self.order <= other.order

    def __gt__(self, other):
        return self.order > other.order

    def __ge__(self, other):
        return self.order >= other.order

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return str(self.title)

    class Meta:
        unique_together = (
            ("menu", "order"),
            ("menu", "title"),
        )
        ordering = ["order"]


class Configuration(SingletonModel):
    """
    A model used for managing the Geonode instance's global configuration,
    without a need for reloading the instance.

    Usage:
    from geonode.base.models import Configuration
    config = Configuration.load()
    """

    read_only = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Configuration"

    def __str__(self):
        return "Configuration"


class UserGeoLimit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False, on_delete=models.CASCADE)
    resource = models.ForeignKey(ResourceBase, null=False, blank=False, on_delete=models.CASCADE)
    wkt = models.TextField(db_column="wkt", blank=True)


class GroupGeoLimit(models.Model):
    group = models.ForeignKey(GroupProfile, null=False, blank=False, on_delete=models.CASCADE)
    resource = models.ForeignKey(ResourceBase, null=False, blank=False, on_delete=models.CASCADE)
    wkt = models.TextField(db_column="wkt", blank=True)


class ExtraMetadata(models.Model):
    resource = models.ForeignKey(ResourceBase, null=False, blank=False, on_delete=models.CASCADE)
    metadata = JSONField(null=True, default=dict, blank=True)
