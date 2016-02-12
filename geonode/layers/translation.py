from modeltranslation.translator import translator, TranslationOptions
from geonode.layers.models import Layer


class LayerTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'abstract',
        'purpose',
        'constraints_other',
        'supplemental_information',
        'data_quality_statement',
    )

translator.register(Layer, LayerTranslationOptions)
