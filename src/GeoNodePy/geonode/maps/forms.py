from django import forms

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

class Proxy(object):
    def __init__(self, wrapped):
        self.__wrapped = wrapped

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

class LabelledWidget(Proxy):
    def __init__(self, label, wrapped):
        super(LabelledWidget, self).__init__(wrapped)
        self.label = label
        self.__wrapped = wrapped

    def render(self, name, value, attrs=None):
        label_html = "<label for='%s'>%s</label>" % (name, self.label) 
        return "<div>" + label_html + self.__wrapped.render(name, value, attrs) + "</div>"

class ContactWidget(forms.MultiWidget):

    def __init__(self, attrs=None, date_format=None, time_format=None):
        name = LabelledWidget("Name", forms.TextInput(attrs))
        organization = LabelledWidget("Organization", forms.TextInput(attrs))
        position = LabelledWidget("Position", forms.TextInput(attrs))
        voice = LabelledWidget("Phone Number (Voice)", forms.TextInput(attrs))
        facsimile = LabelledWidget("Phone Number (Fax)", forms.TextInput(attrs))
        delivery_point = LabelledWidget("Delivery Point", forms.TextInput(attrs))
        city = LabelledWidget("City", forms.TextInput(attrs))
        administrative_area = LabelledWidget("Administrative Area", forms.TextInput(attrs))
        postal_code = LabelledWidget("Postal Code", forms.TextInput(attrs))
        country = LabelledWidget("Country", forms.TextInput(attrs))
        email = LabelledWidget("Email", forms.TextInput(attrs))
        role = LabelledWidget("Role", forms.Select(attrs, [(x, x) for x in ROLE_VALUES]))

        if date_format:
            self.date_format = date_format
        if time_format:
            self.time_format = time_format
        widgets = (
            name, organization, position, voice, facsimile,
            delivery_point, city, administrative_area, postal_code,
            country, email, role
        )
        super(ContactWidget, self).__init__(widgets, attrs)

    def decompress(self, value): 
        if value is None: 
            return [None for x in CONTACT_FIELDS]
        else:
            return [getattr(value, name) for name in CONTACT_FIELDS]

class ContactField(forms.MultiValueField):
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

    fields = [
        name,
        organization,
        position,
        voice,
        facsimile,
        delivery_point,
        city,
        administrative_area,
        postal_code,
        country,
        email,
        role
    ]

    widget = ContactWidget

    def compress(values): 
        if not (values[0] or values[1]):
            raise forms.ValidationError("The contact information must "
                "include either an individual or organization name, or "
                "both."
            )

        values = zip(CONTACT_FIELDS, values)

        contact = Contact()
        for name, value in values:
            setattr(contact, name, value)
        return contact


class MetadataForm(forms.Form):
    title = forms.CharField(300)
    date = forms.DateField()
    date_type = forms.ChoiceField(choices=[(x, x) for x in ['Creation', 'Publication', 'Revision']])
    edition = forms.CharField(300, required=False)
    abstract = forms.CharField(5000, widget=forms.Textarea)
    purpose = forms.CharField(300, required=False)
    poc = ContactField()
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

    metadata_provider = ContactField()
