from modeltranslation.translator import translator, TranslationOptions
from geonode.layers.models import Layer


class LayerTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'abstract',
        'purpose',
        'constraints_other',
        'supplemental_information',
        'distribution_description',
        'data_quality_statement',
    )

translator.register(Layer, LayerTranslationOptions)
