from modeltranslation.translator import translator, TranslationOptions
from geonode.maps.models import Map


class MapTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'abstract',
        'purpose',
        'constraints_other',
        'supplemental_information',
        'distribution_description',
        'data_quality_statement',
    )

translator.register(Map, MapTranslationOptions)
