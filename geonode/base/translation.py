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
