from modeltranslation.translator import translator, TranslationOptions
from geonode.documents.models import Document 

class DocumentTranslationOptions(TranslationOptions):
    fields = ('title', 'abstract', 'purpose', 'constraints_other', 'supplemental_information', 'distribution_description', 'data_quality_statement', )

    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

translator.register(Document, DocumentTranslationOptions)
