from modeltranslation.translator import translator, TranslationOptions
from geonode.base.models import TopicCategory, SpatialRepresentationType, Region, RestrictionCodeType, ResourceBase, License

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

class ResourceBaseTranslationOptions(TranslationOptions):
    fields = ('title', 'abstract', 'purpose', 'constraints_other', 'supplemental_information', 'distribution_description', 'data_quality_statement', )

translator.register(TopicCategory, TopicCategoryTranslationOptions)
translator.register(SpatialRepresentationType, SpatialRepresentationTypeTranslationOptions)
translator.register(Region, RegionTranslationOptions)
translator.register(RestrictionCodeType, RestrictionCodeTypeTranslationOptions)
translator.register(License, LicenseTranslationOptions)
translator.register(ResourceBase, ResourceBaseTranslationOptions)
