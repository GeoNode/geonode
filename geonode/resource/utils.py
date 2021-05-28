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
from django.conf import settings
from django.db import IntegrityError, transaction

from ..base.models import (
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
    HierarchicalKeyword,
    SpatialRepresentationType)

from ..layers.utils import resolve_regions
from ..layers.metadata import convert_keyword


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
                self.instance.keywords.add(*keywords)
        return keywords

    def _set_tkeyword(self, tkeyword):
        if len(tkeyword) > 0:
            if not self.instance.tkeywords:
                self.instance.tkeywords = tkeyword
            else:
                self.instance.tkeywords.add(*tkeyword)
        return [t.alt_label for t in tkeyword]


def update_layer_with_xml_info(instance, xml_file, regions, keywords, vals):
    # Updating layer with information coming from the XML file
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

        # Assign the keywords (needs to be done after saving)
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

        # Save all the modified information in the instance without triggering signals.
        try:
            if hasattr(instance, 'title') and not defaults.get('title', instance.title):
                defaults['title'] = instance.title or getattr(instance, 'name', "")
            if hasattr(instance, 'abstract') and not defaults.get('abstract', instance.abstract):
                defaults['abstract'] = instance.abstract or ''

            to_update = {}
            if hasattr(instance, 'charset'):
                to_update['charset'] = defaults.pop('charset', instance.charset)
            if hasattr(instance, 'storeType'):
                to_update['storeType'] = defaults.pop('storeType', instance.storeType)
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
                instance._class_.objects.filter(id=instance.id).update(**to_update)

                # Refresh from DB
                instance.refresh_from_db()
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
