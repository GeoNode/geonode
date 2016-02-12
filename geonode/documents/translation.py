from modeltranslation.translator import translator, TranslationOptions
from geonode.documents.models import Document


class DocumentTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'abstract',
        'purpose',
        'constraints_other',
        'supplemental_information',
        'data_quality_statement',
    )

translator.register(Document, DocumentTranslationOptions)
