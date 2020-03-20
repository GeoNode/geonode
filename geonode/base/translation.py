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

from modeltranslation.translator import translator, TranslationOptions
from geonode.base.models import (TopicCategory, SpatialRepresentationType, Region,
                                 RestrictionCodeType, License, ResourceBase)


class TopicCategoryTranslationOptions(TranslationOptions):
    fields = ('description', 'gn_description',)


class SpatialRepresentationTypeTranslationOptions(TranslationOptions):
    fields = ('description', 'gn_description',)


class RegionTranslationOptions(TranslationOptions):
    fields = ('name',)


class RestrictionCodeTypeTranslationOptions(TranslationOptions):
    fields = ('description', 'gn_description',)


class LicenseTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'license_text',)


translator.register(TopicCategory, TopicCategoryTranslationOptions)
translator.register(SpatialRepresentationType, SpatialRepresentationTypeTranslationOptions)
translator.register(Region, RegionTranslationOptions)
translator.register(RestrictionCodeType, RestrictionCodeTypeTranslationOptions)
translator.register(License, LicenseTranslationOptions)
translator.register(ResourceBase)
