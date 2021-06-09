# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import re
import logging
import datetime
import traceback

from django.utils import timezone

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.db import IntegrityError, transaction

from ..base.models import (
    Region,
    License,
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
    HierarchicalKeyword,
    SpatialRepresentationType)

from ..layers.models import Layer
from ..layers.utils import resolve_regions
from ..layers.metadata import convert_keyword

logger = logging.getLogger(__name__)


class KeywordHandler:
    '''
    Object needed to handle the keywords coming from the XML
    The expected input are:
     - instance (Layer/Document/Map): instance of any object inherited from ResourceBase.
     - keywords (list(dict)): Is required to analyze the keywords to find if some thesaurus is available.
    '''

    def __init__(self, instance, keywords):
        self.instance = instance
        self.keywords = keywords

    def set_keywords(self):
        '''
        Method with the responsible to set the keywords (free and thesaurus) to the object.
        At return there is always a call to final_step to let it hookable.
        '''
        keywords, tkeyword = self.handle_metadata_keywords()
        self._set_free_keyword(keywords)
        self._set_tkeyword(tkeyword)
        return self.instance

    def handle_metadata_keywords(self):
        '''
        Method the extract the keyword from the dict.
        If the keyword are passed, try to extract them from the dict
        by splitting free-keyword from the thesaurus
        '''
        fkeyword = []
        tkeyword = []
        if len(self.keywords) > 0:
            for dkey in self.keywords:
                if isinstance(dkey, HierarchicalKeyword):
                    fkeyword += [dkey.name]
                    continue
                if isinstance(dkey, str):
                    fkeyword += [dkey]
                    continue
                if dkey['type'] == 'place':
                    continue
                thesaurus = dkey['thesaurus']
                if thesaurus['date'] or thesaurus['datetype'] or thesaurus['title']:
                    for k in dkey['keywords']:
                        tavailable = self.is_thesaurus_available(thesaurus, k)
                        if tavailable.exists():
                            tkeyword += [tavailable.first()]
                        else:
                            fkeyword += [k]
                else:
                    fkeyword += dkey['keywords']
            return fkeyword, tkeyword
        return self.keywords, []

    @staticmethod
    def is_thesaurus_available(thesaurus, keyword):
        is_available = ThesaurusKeyword.objects.filter(alt_label=keyword).filter(thesaurus__title=thesaurus['title'])
        return is_available

    def _set_free_keyword(self, keywords):
        if len(keywords) > 0:
            if not self.instance.keywords:
                self.instance.keywords = keywords
            else:
                self.instance.keywords.clear()
                self.instance.keywords.add(*keywords)
        return keywords

    def _set_tkeyword(self, tkeyword):
        if len(tkeyword) > 0:
            if not self.instance.tkeywords:
                self.instance.tkeywords = tkeyword
            else:
                self.instance.tkeywords.add(*tkeyword)
        return [t.alt_label for t in tkeyword]


def update_resource(instance: ResourceBase, xml_file: str = None, regions: list = [], keywords: list = [], vals: dict = {}):

    if xml_file:
        instance.metadata_xml = open(xml_file).read()

    regions_resolved, regions_unresolved = resolve_regions(regions)
    keywords.extend(convert_keyword(regions_unresolved))

    # Assign the regions (needs to be done after saving)
    regions_resolved = list(set(regions_resolved))
    if regions_resolved:
        if len(regions_resolved) > 0:
            if not instance.regions:
                instance.regions = regions_resolved
            else:
                instance.regions.clear()
                instance.regions.add(*regions_resolved)

    instance = KeywordHandler(instance, keywords).set_keywords()

    # set model properties
    defaults = {}
    for key, value in vals.items():
        if key == 'spatial_representation_type':
            value = SpatialRepresentationType(identifier=value)
        elif key == 'topic_category':
            value, created = TopicCategory.objects.get_or_create(
                identifier=value,
                defaults={'description': '', 'gn_description': value})
            key = 'category'
            defaults[key] = value
        else:
            defaults[key] = value

    poc = defaults.pop('poc', None)
    metadata_author = defaults.pop('metadata_author', None)

    # Save all the modified information in the instance without triggering signals.
    try:
        if hasattr(instance, 'title') and not defaults.get('title', instance.title):
            defaults['title'] = instance.title or getattr(instance, 'name', "")
        if hasattr(instance, 'abstract') and not defaults.get('abstract', instance.abstract):
            defaults['abstract'] = instance.abstract or ''
        if hasattr(instance, 'date') and not defaults.get('date'):
            defaults['date'] = instance.date or timezone.now()

        to_update = {}
        if hasattr(instance, 'charset'):
            to_update['charset'] = defaults.pop('charset', instance.charset)
        if hasattr(instance, 'storeType'):
            to_update['storeType'] = defaults.pop('storeType', instance.storeType)
        if isinstance(instance, Layer):
            for _key in ('name', 'workspace', 'store', 'storeType', 'alternate', 'typename'):
                if _key in defaults:
                    to_update[_key] = defaults.pop(_key)
                else:
                    to_update[_key] = getattr(instance, _key)
        to_update.update(defaults)

        with transaction.atomic():
            ResourceBase.objects.filter(
                id=instance.resourcebase_ptr.id).update(
                **defaults)

            instance.get_real_concrete_instance_class().objects.filter(id=instance.id).update(**to_update)

            # Refresh from DB
            instance.refresh_from_db()
            if poc:
                instance.poc = poc
            if metadata_author:
                instance.metadata_author = metadata_author
    except IntegrityError:
        raise
    return instance


def metadata_storers(instance, custom={}):
    from django.utils.module_loading import import_string
    available_storers = (
        settings.METADATA_STORERS
        if hasattr(settings, "METADATA_STORERS")
        else []
    )
    for storer_path in available_storers:
        storer = import_string(storer_path)
        storer(instance, custom)
    return instance


def resourcebase_post_save(instance, *args, **kwargs):
    """
    Used to fill any additional fields after the save.
    Has to be called by the children
    """
    try:
        # set default License if no specified
        if instance.license is None:
            license = License.objects.filter(name="Not Specified")

            if license and len(license) > 0:
                instance.license = license[0]

        ResourceBase.objects.filter(id=instance.id).update(
            thumbnail_url=instance.get_thumbnail_url(),
            detail_url=instance.get_absolute_url(),
            csw_insert_date=datetime.datetime.now(timezone.get_current_timezone()),
            license=instance.license)
        instance.refresh_from_db()
    except Exception:
        tb = traceback.format_exc()
        if tb:
            logger.debug(tb)
    finally:
        instance.set_missing_info()

    try:
        if not instance.regions or instance.regions.count() == 0:
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
                except Exception:
                    tb = traceback.format_exc()
                    if tb:
                        logger.debug(tb)
            if regions_to_add or global_regions:
                if regions_to_add and len(
                        regions_to_add) > 0 and len(regions_to_add) <= 30:
                    instance.regions.add(*regions_to_add)
                else:
                    instance.regions.add(*global_regions)
    except Exception:
        tb = traceback.format_exc()
        if tb:
            logger.debug(tb)
    finally:
        # refresh catalogue metadata records
        from geonode.catalogue.models import catalogue_post_save
        catalogue_post_save(instance=instance, sender=instance.__class__)
