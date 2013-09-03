.. _localization:

============
Localization
============

To enable a new language in GeoNode you have to do the following:

#. Install gettext::

    sudo apt-get install gettext

#. Create a directory named locale in the root of your project::

    mkdir locale

#. In the root of your project, run::

    python manage.py makemessages -l fr

#. Navigate to the GeoNode dir and do::

    cd src/GeoNodePy/geonode/maps; django-admin.py makemessages -l fr
    cd src/GeoNodePy/geonode; django-admin.py makemessages -l fr

Optional steps:

#. Install django-rossetta::

    http://code.google.com/p/django-rosetta/

#. Install django-modeltranslation

#. If you want to enable metadata in the other format too, make sure you have model translation installed and create a translations.py file like this::

    from modeltranslation.translator import translator, TranslationOptions
    from geonode.maps.models import Layer

    class LayerTO(TranslationOptions):
        fields = (
                 'title',
                 'edition',
                 'abstract',
                 'purpose',
                 'constraints_other',
                 'distribution_description',
                 'data_quality_statement',
                 'supplemental_information',
                 )

    translator.register(FlatBlock, FlatBlockTO)
    translator.register(Layer, LayerTO)
