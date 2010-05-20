from django import forms
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

ROLE_VALUES = [
    'datasetProvider',
    'custodian',
    'owner',
    'user',
    'distributor',
    'originator',
    'pointOfContact',
    'principalInvestigator',
    'processor',
    'publisher',
    'author'
]

UPDATE_FREQUENCIES = [
    'annually',
    'asNeeded',
    'biannually',
    'continual',
    'daily',
    'fortnightly',
    'irregular',
    'monthly',
    'notPlanned',
    'quarterly',
    'unknown',
    'weekly'
]

CONSTRAINT_OPTIONS = [
    'copyright',
    'intellectualPropertyRights',
    'license',
    'otherRestrictions',
    'patent',
    'patentPending',
    'restricted',
    'trademark'
]

SPATIAL_REPRESENTATION_TYPES = [
    'grid', 'steroModel', 'textTable', 'tin', 'vector'
]

TOPIC_CATEGORIES = [
    'biota',
    'boundaries',
    'climatologyMeteorologicalAtmosphere',
    'economy',
    'elevation',
    'environment',
    'farming',
    'geoscientificInformation',
    'health',
    'imageryBaseMapsEarthCover',
    'inlandWaters',
    'intelligenceMilitary',
    'location',
    'oceans',
    'planningCadastre'
    'society',
    'structure',
    'transportation',
    'utilitiesCommunication'
]

CONTACT_FIELDS = [
    "name",
    "organization",
    "position",
    "voice",
    "facsimile",
    "delivery_point",
    "city",
    "administrative_area",
    "postal_code",
    "country",
    "email",
    "role"
]

def require(*args):
    pass

class Contact(object): pass

class LabelledInput(forms.Widget):
    def __init__(self, name, attrs=None):
        # The 'rows' and 'cols' attributes are required for HTML correctness.
        self.name = name
        super(LabelledInput, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs)
        return mark_safe( u'<label for="{id}">{name}</label> <input name="{name}"{atts}>{value}</input>'.format(
            id = final_attrs.get(id, ""),
            name = self.name,
            atts = flatatt(final_attrs),
            value = conditional_escape(force_unicode(value))
        ))


class ContactForm(forms.Form):
    name = forms.CharField(300)
    organization = forms.CharField(300)
    position = forms.CharField(300, required=False)
    voice = forms.CharField(300, required=False)
    facsimile = forms.CharField(300, required=False)
    delivery_point = forms.CharField(300, required=False)
    city = forms.CharField(300, required=False)
    administrative_area = forms.CharField(300, required=False)
    postal_code = forms.CharField(300, required=False)
    country = forms.CharField(300, required=False)
    email = forms.CharField(300, required=False)
    role = forms.ChoiceField(choices= [(x, x) for x in ROLE_VALUES])


class MetadataForm(forms.Form):
    title = forms.CharField(300)
    date = forms.DateField()
    date_type = forms.ChoiceField(choices=[(x, x) for x in ['Creation', 'Publication', 'Revision']])
    edition = forms.CharField(300, required=False)
    abstract = forms.CharField(5000, widget=forms.Textarea)
    purpose = forms.CharField(300, required=False)
    maintenance_frequency = forms.ChoiceField(choices = [(x, x) for x in UPDATE_FREQUENCIES])
    keywords = forms.CharField(300, required=False)
    keywords_region = forms.ChoiceField() #TODO: Get list of country codes
    constraints_use = forms.ChoiceField(choices = [(x, x) for x in CONSTRAINT_OPTIONS])
    constraints_other = forms.CharField(5000, widget=forms.Textarea, required=False)
    spatial_representation_type = forms.ChoiceField(choices=[(x,x) for x in SPATIAL_REPRESENTATION_TYPES], required=False)
    language = forms.ChoiceField() # TODO: Get list of language codes
    topic_category = forms.ChoiceField(choices = [(x, x) for x in TOPIC_CATEGORIES])
    temporal_extent_start = forms.DateField(required=False)
    temporal_extent_end = forms.DateField(required=False)
    geographic_bounding_box = forms.CharField(300) # hmmm.
    supplemental_information = forms.CharField(5000)

    distribution_url = forms.CharField(300, required=False)
    distribution_description = forms.CharField(5000, required=False)

    data_quality_statement = forms.CharField(5000, required=False)

    # poc - use a ContactForm
    # metadata_provider - use a ContactForm
