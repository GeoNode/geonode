# -*- coding: UTF-8 -*-
from django.conf import settings
from django.db import models
from owslib.wms import WebMapService
from owslib.csw import CatalogueServiceWeb
from geoserver.catalog import Catalog
from geonode.core.models import PermissionLevelMixin
from geonode.core.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.geonetwork import Catalog as GeoNetwork
from django.db.models import signals
import httplib2
import simplejson
import urllib
import uuid
import datetime
from django.contrib.auth.models import User, Permission
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

def bbox_to_wkt(x0, x1, y0, y1, srid="4326"):
    return 'SRID=%s;POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))' % (srid,
                            x0, y0, x0, y1, x1, y1, x1, y0, x0, y0)

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

COUNTRIES = (
    ('AFG', _('Afghanistan')), 
    ('ALA', _('Aland Islands')),
    ('ALB', _('Albania')),
    ('DZA', _('Algeria')),
    ('ASM', _('American Samoa')),
    ('AND', _('Andorra')),
    ('AGO', _('Angola')),
    ('AIA', _('Anguilla')),
    ('ATG', _('Antigua and Barbuda')),
    ('ARG', _('Argentina')),
    ('ARM', _('Armenia')),
    ('ABW', _('Aruba')),
    ('AUS', _('Australia')),
    ('AUT', _('Austria')),
    ('AZE', _('Azerbaijan')),
    ('BHS', _('Bahamas')),
    ('BHR', _('Bahrain')),
    ('BGD', _('Bangladesh')),
    ('BRB', _('Barbados')),
    ('BLR', _('Belarus')),
    ('BEL', _('Belgium')),
    ('BLZ', _('Belize')),
    ('BEN', _('Benin')),
    ('BMU', _('Bermuda')),
    ('BTN', _('Bhutan')),
    ('BOL', _('Bolivia')),
    ('BIH', _('Bosnia and Herzegovina')),
    ('BWA', _('Botswana')),
    ('BRA', _('Brazil')),
    ('VGB', _('British Virgin Islands')),
    ('BRN', _('Brunei Darussalam')),
    ('BGR', _('Bulgaria')),
    ('BFA', _('Burkina Faso')),
    ('BDI', _('Burundi')),
    ('KHM', _('Cambodia')),
    ('CMR', _('Cameroon')),
    ('CAN', _('Canada')),
    ('CPV', _('Cape Verde')),
    ('CYM', _('Cayman Islands')),
    ('CAF', _('Central African Republic')),
    ('TCD', _('Chad')),
    ('CIL', _('Channel Islands')),
    ('CHL', _('Chile')),
    ('CHN', _('China')),
    ('HKG', _('China - Hong Kong')),
    ('MAC', _('China - Macao')),
    ('COL', _('Colombia')),
    ('COM', _('Comoros')),
    ('COG', _('Congo')),
    ('COK', _('Cook Islands')),
    ('CRI', _('Costa Rica')),
    ('CIV', _('Cote d\'Ivoire')),
    ('HRV', _('Croatia')),
    ('CUB', _('Cuba')),
    ('CYP', _('Cyprus')),
    ('CZE', _('Czech Republic')),
    ('PRK', _('Democratic People\'s Republic of Korea')),
    ('COD', _('Democratic Republic of the Congo')),
    ('DNK', _('Denmark')),
    ('DJI', _('Djibouti')),
    ('DMA', _('Dominica')),
    ('DOM', _('Dominican Republic')),
    ('ECU', _('Ecuador')),
    ('EGY', _('Egypt')),
    ('SLV', _('El Salvador')),
    ('GNQ', _('Equatorial Guinea')),
    ('ERI', _('Eritrea')),
    ('EST', _('Estonia')),
    ('ETH', _('Ethiopia')),
    ('FRO', _('Faeroe Islands')),
    ('FLK', _('Falkland Islands (Malvinas)')),
    ('FJI', _('Fiji')),
    ('FIN', _('Finland')),
    ('FRA', _('France')),
    ('GUF', _('French Guiana')),
    ('PYF', _('French Polynesia')),
    ('GAB', _('Gabon')),
    ('GMB', _('Gambia')),
    ('GEO', _('Georgia')),
    ('DEU', _('Germany')),
    ('GHA', _('Ghana')),
    ('GIB', _('Gibraltar')),
    ('GRC', _('Greece')),
    ('GRL', _('Greenland')),
    ('GRD', _('Grenada')),
    ('GLP', _('Guadeloupe')),
    ('GUM', _('Guam')),
    ('GTM', _('Guatemala')),
    ('GGY', _('Guernsey')),
    ('GIN', _('Guinea')),
    ('GNB', _('Guinea-Bissau')),
    ('GUY', _('Guyana')),
    ('HTI', _('Haiti')),
    ('VAT', _('Holy See (Vatican City)')),
    ('HND', _('Honduras')),
    ('HUN', _('Hungary')),
    ('ISL', _('Iceland')),
    ('IND', _('India')),
    ('IDN', _('Indonesia')),
    ('IRN', _('Iran')),
    ('IRQ', _('Iraq')),
    ('IRL', _('Ireland')),
    ('IMN', _('Isle of Man')),
    ('ISR', _('Israel')),
    ('ITA', _('Italy')),
    ('JAM', _('Jamaica')),
    ('JPN', _('Japan')),
    ('JEY', _('Jersey')),
    ('JOR', _('Jordan')),
    ('KAZ', _('Kazakhstan')),
    ('KEN', _('Kenya')),
    ('KIR', _('Kiribati')),
    ('KWT', _('Kuwait')),
    ('KGZ', _('Kyrgyzstan')),
    ('LAO', _('Lao People\'s Democratic Republic')),
    ('LVA', _('Latvia')),
    ('LBN', _('Lebanon')),
    ('LSO', _('Lesotho')),
    ('LBR', _('Liberia')),
    ('LBY', _('Libyan Arab Jamahiriya')),
    ('LIE', _('Liechtenstein')),
    ('LTU', _('Lithuania')),
    ('LUX', _('Luxembourg')),
    ('MKD', _('Macedonia')),
    ('MDG', _('Madagascar')),
    ('MWI', _('Malawi')),
    ('MYS', _('Malaysia')),
    ('MDV', _('Maldives')),
    ('MLI', _('Mali')),
    ('MLT', _('Malta')),
    ('MHL', _('Marshall Islands')),
    ('MTQ', _('Martinique')),
    ('MRT', _('Mauritania')),
    ('MUS', _('Mauritius')),
    ('MYT', _('Mayotte')),
    ('MEX', _('Mexico')),
    ('FSM', _('Micronesia, Federated States of')),
    ('MCO', _('Monaco')),
    ('MNG', _('Mongolia')),
    ('MNE', _('Montenegro')),
    ('MSR', _('Montserrat')),
    ('MAR', _('Morocco')),
    ('MOZ', _('Mozambique')),
    ('MMR', _('Myanmar')),
    ('NAM', _('Namibia')),
    ('NRU', _('Nauru')),
    ('NPL', _('Nepal')),
    ('NLD', _('Netherlands')),
    ('ANT', _('Netherlands Antilles')),
    ('NCL', _('New Caledonia')),
    ('NZL', _('New Zealand')),
    ('NIC', _('Nicaragua')),
    ('NER', _('Niger')),
    ('NGA', _('Nigeria')),
    ('NIU', _('Niue')),
    ('NFK', _('Norfolk Island')),
    ('MNP', _('Northern Mariana Islands')),
    ('NOR', _('Norway')),
    ('PSE', _('Occupied Palestinian Territory')),
    ('OMN', _('Oman')),
    ('PAK', _('Pakistan')),
    ('PLW', _('Palau')),
    ('PAN', _('Panama')),
    ('PNG', _('Papua New Guinea')),
    ('PRY', _('Paraguay')),
    ('PER', _('Peru')),
    ('PHL', _('Philippines')),
    ('PCN', _('Pitcairn')),
    ('POL', _('Poland')),
    ('PRT', _('Portugal')),
    ('PRI', _('Puerto Rico')),
    ('QAT', _('Qatar')),
    ('KOR', _('Republic of Korea')),
    ('MDA', _('Republic of Moldova')),
    ('REU', _('Reunion')),
    ('ROU', _('Romania')),
    ('RUS', _('Russian Federation')),
    ('RWA', _('Rwanda')),
    ('BLM', _('Saint-Barthelemy')),
    ('SHN', _('Saint Helena')),
    ('KNA', _('Saint Kitts and Nevis')),
    ('LCA', _('Saint Lucia')),
    ('MAF', _('Saint-Martin (French part)')),
    ('SPM', _('Saint Pierre and Miquelon')),
    ('VCT', _('Saint Vincent and the Grenadines')),
    ('WSM', _('Samoa')),
    ('SMR', _('San Marino')),
    ('STP', _('Sao Tome and Principe')),
    ('SAU', _('Saudi Arabia')),
    ('SEN', _('Senegal')),
    ('SRB', _('Serbia')),
    ('SYC', _('Seychelles')),
    ('SLE', _('Sierra Leone')),
    ('SGP', _('Singapore')),
    ('SVK', _('Slovakia')),
    ('SVN', _('Slovenia')),
    ('SLB', _('Solomon Islands')),
    ('SOM', _('Somalia')),
    ('ZAF', _('South Africa')),
    ('ESP', _('Spain')),
    ('LKA', _('Sri Lanka')),
    ('SDN', _('Sudan')),
    ('SUR', _('Suriname')),
    ('SJM', _('Svalbard and Jan Mayen Islands')),
    ('SWZ', _('Swaziland')),
    ('SWE', _('Sweden')),
    ('CHE', _('Switzerland')),
    ('SYR', _('Syrian Arab Republic')),
    ('TJK', _('Tajikistan')),
    ('THA', _('Thailand')),
    ('TLS', _('Timor-Leste')),
    ('TGO', _('Togo')),
    ('TKL', _('Tokelau')),
    ('TON', _('Tonga')),
    ('TTO', _('Trinidad and Tobago')),
    ('TUN', _('Tunisia')),
    ('TUR', _('Turkey')),
    ('TKM', _('Turkmenistan')),
    ('TCA', _('Turks and Caicos Islands')),
    ('TUV', _('Tuvalu')),
    ('UGA', _('Uganda')),
    ('UKR', _('Ukraine')),
    ('ARE', _('United Arab Emirates')),
    ('GBR', _('United Kingdom')),
    ('TZA', _('United Republic of Tanzania')),
    ('USA', _('United States of America')),
    ('VIR', _('United States Virgin Islands')),
    ('URY', _('Uruguay')),
    ('UZB', _('Uzbekistan')),
    ('VUT', _('Vanuatu')),
    ('VEN', _('Venezuela (Bolivarian Republic of)')),
    ('VNM', _('Viet Nam')),
    ('WLF', _('Wallis and Futuna Islands')),
    ('ESH', _('Western Sahara')),
    ('YEM', _('Yemen')),
    ('ZMB', _('Zambia')),
    ('ZWE', _('Zimbabwe')),
)

# Taken from http://www.w3.org/WAI/ER/IG/ert/iso639.htm
ALL_LANGUAGES = (
    ('abk', 'Abkhazian'),
    ('aar', 'Afar'),
    ('afr', 'Afrikaans'),
    ('amh', 'Amharic'),
    ('ara', 'Arabic'),
    ('asm', 'Assamese'),
    ('aym', 'Aymara'),
    ('aze', 'Azerbaijani'),
    ('bak', 'Bashkir'),
    ('ben', 'Bengali'),
    ('bih', 'Bihari'),
    ('bis', 'Bislama'),
    ('bre', 'Breton'),
    ('bul', 'Bulgarian'),
    ('bel', 'Byelorussian'),
    ('cat', 'Catalan'),
    ('cos', 'Corsican'),
    ('dan', 'Danish'),
    ('dzo', 'Dzongkha'),
    ('eng', 'English'),
    ('epo', 'Esperanto'),
    ('est', 'Estonian'),
    ('fao', 'Faroese'),
    ('fij', 'Fijian'),
    ('fin', 'Finnish'),
    ('fry', 'Frisian'),
    ('glg', 'Gallegan'),
    ('kal', 'Greenlandic'),
    ('grn', 'Guarani'),
    ('guj', 'Gujarati'),
    ('hau', 'Hausa'),
    ('heb', 'Hebrew'),
    ('hin', 'Hindi'),
    ('hun', 'Hungarian'),
    ('ind', 'Indonesian'),
    ('ina', 'Interlingua (International Auxiliary language Association)'),
    ('iku', 'Inuktitut'),
    ('ipk', 'Inupiak'),
    ('ita', 'Italian'),
    ('jpn', 'Japanese'),
    ('kan', 'Kannada'),
    ('kas', 'Kashmiri'),
    ('kaz', 'Kazakh'),
    ('khm', 'Khmer'),
    ('kin', 'Kinyarwanda'),
    ('kir', 'Kirghiz'),
    ('kor', 'Korean'),
    ('kur', 'Kurdish'),
    ('oci', 'Langue d \'Oc (post 1500)'),
    ('lao', 'Lao'),
    ('lat', 'Latin'),
    ('lav', 'Latvian'),
    ('lin', 'Lingala'),
    ('lit', 'Lithuanian'),
    ('mlg', 'Malagasy'),
    ('mlt', 'Maltese'),
    ('mar', 'Marathi'),
    ('mol', 'Moldavian'),
    ('mon', 'Mongolian'),
    ('nau', 'Nauru'),
    ('nep', 'Nepali'),
    ('nor', 'Norwegian'),
    ('ori', 'Oriya'),
    ('orm', 'Oromo'),
    ('pan', 'Panjabi'),
    ('pol', 'Polish'),
    ('por', 'Portuguese'),
    ('pus', 'Pushto'),
    ('que', 'Quechua'),
    ('roh', 'Rhaeto-Romance'),
    ('run', 'Rundi'),
    ('rus', 'Russian'),
    ('smo', 'Samoan'),
    ('sag', 'Sango'),
    ('san', 'Sanskrit'),
    ('scr', 'Serbo-Croatian'),
    ('sna', 'Shona'),
    ('snd', 'Sindhi'),
    ('sin', 'Singhalese'),
    ('ssw', 'Siswant'),
    ('slv', 'Slovenian'),
    ('som', 'Somali'),
    ('sot', 'Sotho'),
    ('sun', 'Sudanese'),
    ('swa', 'Swahili'),
    ('tgl', 'Tagalog'),
    ('tgk', 'Tajik'),
    ('tam', 'Tamil'),
    ('tat', 'Tatar'),
    ('tel', 'Telugu'),
    ('tha', 'Thai'),
    ('tir', 'Tigrinya'),
    ('tog', 'Tonga (Nyasa)'),
    ('tso', 'Tsonga'),
    ('tsn', 'Tswana'),
    ('tur', 'Turkish'),
    ('tuk', 'Turkmen'),
    ('twi', 'Twi'),
    ('uig', 'Uighur'),
    ('ukr', 'Ukrainian'),
    ('urd', 'Urdu'),
    ('uzb', 'Uzbek'),
    ('vie', 'Vietnamese'),
    ('vol', 'Volapük'),
    ('wol', 'Wolof'),
    ('xho', 'Xhosa'),
    ('yid', 'Yiddish'),
    ('yor', 'Yoruba'),
    ('zha', 'Zhuang'),
    ('zul', 'Zulu'),
)

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

DEFAULT_SUPPLEMENTAL_INFORMATION=_(
'You can customize the template to suit your \
needs. You can add and remove fields and fill out default \
information (e.g. contact details). Fields you can not change in \
the default view may be accessible in the more comprehensive (and \
more complex) advanced view. You can even use the XML editor to \
create custom structures, but they have to be validated by the \
system, so know what you do :-)'
)


class Contact(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    name = models.CharField('Individual Name', max_length=255, blank=True, null=True)
    organization = models.CharField('Organization Name', max_length=255, blank=True, null=True)
    position = models.CharField('Position Name', max_length=255, blank=True, null=True)
    voice = models.CharField('Voice', max_length=255, blank=True, null=True)
    fax = models.CharField('Facsimile',  max_length=255, blank=True, null=True)
    delivery = models.CharField('Delivery Point', max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField('Administrative Area', max_length=255, blank=True, null=True)
    zipcode = models.CharField('Postal Code', max_length=255, blank=True, null=True)
    country = models.CharField(choices=COUNTRIES, max_length=3, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def clean(self):
        # the specification says that either name or organization should be provided
        valid_name = (self.name != None and self.name != '')
        valid_organization = (self.organization != None and self.organization !='')
        if not (valid_name or valid_organization):
            raise ValidationError('Either name or organization should be provided')
    
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.organization)


def get_csw():
    csw_url = "%ssrv/en/csw" % settings.GEONETWORK_BASE_URL
    csw = CatalogueServiceWeb(csw_url);
    return csw

_wms = None
_csw = None
_user, _password = settings.GEOSERVER_CREDENTIALS

class LayerManager(models.Manager):
    
    def __init__(self):
        models.Manager.__init__(self)
        url = "%srest" % settings.GEOSERVER_BASE_URL
        user, password = settings.GEOSERVER_CREDENTIALS
        self.gs_catalog = Catalog(url, _user, _password)
        self.geonetwork = GeoNetwork(settings.GEONETWORK_BASE_URL, settings.GEONETWORK_CREDENTIALS[0], settings.GEONETWORK_CREDENTIALS[1])

    @property
    def gn_catalog(self):
        # check if geonetwork is logged in
        if not self.geonetwork.connected:
            self.geonetwork.login()
        # Make sure to logout after you have finished using it.
        return self.geonetwork

    def admin_contact(self):
        # this assumes there is at least one superuser
        superusers = User.objects.filter(is_superuser=True).order_by('id')
        if superusers.count() == 0:
            raise RuntimeException('GeoNode needs at least one admin/superuser set')
        
        contact, created = Contact.objects.get_or_create(user=superusers[0], 
                                                defaults={"name": "Geonode Admin"})
        return contact

    def default_poc(self):
        return self.admin_contact()

    def default_metadata_author(self):
        return self.admin_contact()

    def slurp(self):
        cat = self.gs_catalog
        gn = self.gn_catalog
        for resource in cat.get_resources():
            try:
                store = resource.store
                workspace = store.workspace

                layer, created = self.get_or_create(name=resource.name, defaults = {
                    "workspace": workspace.name,
                    "store": store.name,
                    "storeType": store.resource_type,
                    "typename": "%s:%s" % (workspace.name, resource.name),
                    "title": resource.title or 'No title provided',
                    "abstract": resource.abstract or 'No abstract provided',
                    "uuid": str(uuid.uuid4())
                })

                layer.save()
                if created: 
                    layer.set_default_permissions()
            finally:
                pass
        # Doing a logout since we know we don't need this object anymore.
        gn.logout()

class Layer(models.Model, PermissionLevelMixin):
    """
    Layer Object loosely based on ISO 19115:2003
    """
    # internal fields
    objects = LayerManager()
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storeType = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    uuid = models.CharField(max_length=36)
    typename = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(User, blank=True, null=True)

    contacts = models.ManyToManyField(Contact, through='ContactRole')

    # section 1
    title = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now=True)
    date_type = models.CharField(max_length=255,choices=[(x, x) for x in ['Creation', 'Publication', 'Revision']], default='Publication')
    edition = models.CharField(max_length=255, blank=True, null=True)
    abstract = models.TextField()
    purpose = models.TextField(null=True, blank=True)
    maintenance_frequency = models.CharField(max_length=255, choices = [(x, x) for x in UPDATE_FREQUENCIES], blank=True, null=True)

    # section 2
    # see poc property definition below

    # section 3
    keywords = models.TextField(blank=True, null=True)
    keywords_region = models.CharField(max_length=3, choices= COUNTRIES, default = 'USA')
    constraints_use = models.CharField(max_length=255, choices = [(x, x) for x in CONSTRAINT_OPTIONS], default='copyright')
    constraints_other = models.TextField(blank=True, null=True)
    spatial_representation_type = models.CharField(max_length=255, choices=[(x,x) for x in SPATIAL_REPRESENTATION_TYPES], blank=True, null=True)

    # Section 4
    language = models.CharField(max_length=3, choices=ALL_LANGUAGES, default='eng')
    topic_category = models.CharField(max_length=255, choices = [(x, x) for x in TOPIC_CATEGORIES], default = 'location')

    # Section 5
    temporal_extent_start = models.DateField(blank=True, null=True)
    temporal_extent_end = models.DateField(blank=True, null=True)
    geographic_bounding_box = models.TextField()
    supplemental_information = models.TextField(default=DEFAULT_SUPPLEMENTAL_INFORMATION)

    # Section 6
    distribution_url = models.TextField(blank=True, null=True)
    distribution_description = models.TextField(blank=True, null=True)

    # Section 8
    data_quality_statement = models.TextField(blank=True, null=True)

    # Section 9
    # see metadata_author property definition below

    def download_links(self):
        """Returns a list of (mimetype, URL) tuples for downloads of this data
        in various formats."""
 
        bbox = self.resource.latlon_bbox

        dx = float(bbox[1]) - float(bbox[0])
        dy = float(bbox[3]) - float(bbox[2])

        dataAspect = dx / dy

        height = 550
        width = int(height * dataAspect)

        # bbox: this.adjustBounds(widthAdjust, heightAdjust, values.llbbox).toString(),

        srs = 'EPSG:4326' # bbox[4] might be None
        bbox_string = ",".join([bbox[0], bbox[2], bbox[1], bbox[3]])

        links = []        

        if self.resource.resource_type == "featureType":
            def wfs_link(mime):
                return settings.GEOSERVER_BASE_URL + "wfs?" + urllib.urlencode({
                    'service': 'WFS',
                    'request': 'GetFeature',
                    'typename': self.typename,
                    'outputFormat': mime
                })
            types = [
                ("zip", _("Zipped Shapefile"), "SHAPE-ZIP"),
                ("gml", _("GML 2.0"), "gml2")
            ]
            links.extend((ext, name, wfs_link(mime)) for ext, name, mime in types)

        def wms_link(mime):
            return settings.GEOSERVER_BASE_URL + "wms?" + urllib.urlencode({
                'service': 'WMS',
                'request': 'GetMap',
                'layers': self.typename,
                'format': mime,
                'height': height,
                'width': width,
                'srs': srs,
                'bbox': bbox_string
            })

        types = [
            ("kmz", _("Zipped KML"), "application/vnd.google-earth.kmz+xml"),
            ("tiff", _("GeoTiff"), "image/geotiff"),
            ("pdf", _("PDF"), "application/pdf"),
            ("png", _("PNG"), "image/png")
        ]

        links.extend((ext, name, wms_link(mime)) for ext, name, mime in types)

        return links

    def maps(self):
        """Return a list of all the maps that use this layer"""
        local_wms = "%swms" % settings.GEOSERVER_BASE_URL
        return set([layer.map for layer in MapLayer.objects.filter(ows_url=local_wms, name=self.typename).select_related()])

    def metadata(self):
        global _wms
        if (_wms is None) or (self.typename not in _wms.contents):
            wms_url = "%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL
            _wms = WebMapService(wms_url)
        return _wms[self.typename]

    def metadata_csw(self):
        csw = get_csw()
        csw.getrecordbyid([self.uuid], outputschema = 'http://www.isotc211.org/2005/gmd')
        return csw.records.get(self.uuid)

    @property
    def attribute_names(self):
        if self.resource.resource_type == "featureType":
            return self.resource.attributes
        elif self.resource.resource_type == "coverage":
            return [dim.name for dim in self.resource.dimensions]

    @property
    def display_type(self):
        return ({
            "dataStore" : "Vector Data",
            "coverageStore": "Raster Data",
        }).get(self.storeType, "Data")

    def delete_from_geoserver(self):
        layerURL = "%srest/layers/%s.xml" % (settings.GEOSERVER_BASE_URL,self.name)
        if self.storeType == "dataStore":
            featureUrl = "%srest/workspaces/%s/datastores/%s/featuretypes/%s.xml" % (settings.GEOSERVER_BASE_URL, self.workspace, self.store, self.name)
            storeUrl = "%srest/workspaces/%s/datastores/%s.xml" % (settings.GEOSERVER_BASE_URL, self.workspace, self.store)
        elif self.storeType == "coverageStore":
            featureUrl = "%srest/workspaces/%s/coveragestores/%s/coverages/%s.xml" % (settings.GEOSERVER_BASE_URL,self.workspace,self.store, self.name)
            storeUrl = "%srest/workspaces/%s/coveragestores/%s.xml" % (settings.GEOSERVER_BASE_URL,self.workspace,self.store)
        urls = (layerURL,featureUrl,storeUrl)

        # GEOSERVER_CREDENTIALS
        HTTP = httplib2.Http(".cache")
        HTTP.add_credentials(_user,_password)

        for u in urls:
            output = HTTP.request(u,"DELETE")
            if output[0]["status"][0] == '4':
                raise RuntimeError("Unable to remove from Geoserver: %s" % output[1])

    def delete_from_geonetwork(self):
        gn = Layer.objects.gn_catalog
        gn.delete_layer(self)

    def save_to_geonetwork(self):
        gn = Layer.objects.gn_catalog
        record = gn.get_by_uuid(self.uuid)
        if record is None:
            md_link = gn.create_from_layer(self)
            self.metadata_links = [("text/xml", "TC211", md_link)]
        else:
            gn.update_layer(self)

    @property
    def resource(self):
        if not hasattr(self, "_resource_cache"):
            cat = Layer.objects.gs_catalog
            try:
                ws = cat.get_workspace(self.workspace)
            except AttributeError:
                # Geoserver is not running
                raise RuntimeError("Geoserver cannot be accessed, are you sure it is running in: %s" %
                                    (settings.GEOSERVER_BASE_URL))
            store = cat.get_store(self.store, ws)
            self._resource_cache = cat.get_resource(self.name, store)
        return self._resource_cache

    def _get_default_style(self):
        return self.publishing.default_style

    def _set_default_style(self, style):
        self.publishing.default_style = style

    default_style = property(_get_default_style, _set_default_style)

    def _get_styles(self):
        return self.publishing.styles

    def _set_styles(self, styles):
        self.publishing.styles = styles

    styles = property(_get_styles, _set_styles)
    
    @property
    def service_type(self):
        if self.storeType == 'coverageStore':
            return "WCS"
        if self.storeType == 'dataStore':
            return "WFS"

    @property
    def publishing(self):
        if not hasattr(self, "_publishing_cache"):
            cat = Layer.objects.gs_catalog
            self._publishing_cache = cat.get_layer(self.name)
        return self._publishing_cache

    @property
    def poc_role(self):
        role = Role.objects.get(value='pointOfContact')
        return role

    @property
    def metadata_author_role(self):
        role = Role.objects.get(value='author')
        return role

    def _set_poc(self, poc):
        # reset any poc asignation to this layer
        ContactRole.objects.filter(role=self.poc_role, layer=self).delete()
        #create the new assignation
        contact_role = ContactRole.objects.create(role=self.poc_role, layer=self, contact=poc)

    def _get_poc(self):
        try:
            the_poc = ContactRole.objects.get(role=self.poc_role, layer=self).contact
        except ContactRole.DoesNotExist:
            the_poc = None
        return the_poc

    poc = property(_get_poc, _set_poc)

    def _set_metadata_author(self, metadata_author):
        # reset any metadata_author asignation to this layer
        ContactRole.objects.filter(role=self.metadata_author_role, layer=self).delete()
        #create the new assignation
        contact_role = ContactRole.objects.create(role=self.metadata_author_role,
                                                  layer=self, contact=metadata_author)

    def _get_metadata_author(self):
        try:
            the_ma = ContactRole.objects.get(role=self.metadata_author_role, layer=self).contact
        except  ContactRole.DoesNotExist:
            the_ma = None
        return the_ma

    metadata_author = property(_get_metadata_author, _set_metadata_author)

    def save_to_geoserver(self):
        if hasattr(self, "_resource_cache"):
            self.resource.title = self.title
            self.resource.abstract = self.abstract
            self.resource.name= self.name
            Layer.objects.gs_catalog.save(self._resource_cache)
        if hasattr(self, "_publishing_cache"):
            Layer.objects.gs_catalog.save(self._publishing_cache)

    def  _populate_from_gs(self):
        gs_resource = Layer.objects.gs_catalog.get_resource(self.name)
        srs = gs_resource.projection
        if self.geographic_bounding_box is '' or self.geographic_bounding_box is None:
            self.set_bbox(gs_resource.native_bbox, srs=srs)

    def _autopopulate(self):
        if self.poc is None:
            self.poc = Layer.objects.default_poc()
        if self.metadata_author is None:
            self.metadata_author = Layer.objects.default_metadata_author()
        if self.abstract == '' or self.abstract is None:
            self.abstract = 'No abstract provided'
        if self.title == '' or self.title is None:
            self.title = self.name

    def _populate_from_gn(self):
        meta = self.metadata_csw()
        self.keywords = [word for word in meta.identification.keywords['list'] if isinstance(word,str)]
        self.distribution_url = meta.distribution.onlineresource.url
        self.distribution_description = meta.distribution.onlineresource.description

    def set_bbox(self, box, srs=None):
        """
        Sets a bounding box based on the gsconfig native_box param.
        """
        if srs:
            srid = srs
        else:
            srid = box[4]
        self.geographic_bounding_box = bbox_to_wkt(box[0], box[1], box[2], box[3], srid=srid )

    def get_absolute_url(self):
        return "%sdata/%s" % (settings.SITEURL,self.typename)

    def __str__(self):
        return "%s Layer" % self.typename

    class Meta:
        # custom permissions,
        # change and delete are standard in django
        permissions = (('view_layer', 'Can view'), 
                       ('change_layer_permissions', "Can change permissions"), )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ  = 'layer_readonly'
    LEVEL_WRITE = 'layer_readwrite'
    LEVEL_ADMIN = 'layer_admin'
                 
    def set_default_permissions(self):
        self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ) 

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)


class Map(models.Model, PermissionLevelMixin):
    # metadata fields
    title = models.CharField(max_length=200)
    abstract = models.CharField(max_length=200)
    contact = models.CharField(max_length=200)
    
    # These fields are likely deprecated but
    # we need to double check with the World Bank
    # as they were the ones who required them
    featured = models.BooleanField()
    endorsed = models.BooleanField()

    # viewer configuration
    zoom = models.IntegerField()
    center_lat = models.FloatField()
    center_lon = models.FloatField()
    owner = models.ForeignKey(User, blank=True, null=True)

    def __unicode__(self):
        return '%s by %s' % (self.title, self.contact)

    @property
    def layers(self):
        layers = MapLayer.objects.filter(map=self.id)
        return  [layer for layer in layers]

    @property
    def local_layers(self): 
        return True

    @property
    def json(self):
        map_layers = MapLayer.objects.filter(map=self.id)
        layers = [] 
        for map_layer in map_layers:
            if map_layer.local():   
                layer =  Layer.objects.get(typename=map_layer.name)
                layers.append(layer)
            else: 
                pass 
        map = { 
            "map" : { 
                "title" : self.title, 
                "abstract" : self.abstract,
                "author" : "The GeoNode Team",
                }, 
            "layers" : [ 
                {
                    "name" : layer.typename, 
                    "service" : layer.service_type, 
                    "metadataURL" : "http://localhost/fake/url/{name}".format(name=layer.name),
                    "serviceURL" : "http://localhost/%s" %layer.name,
                } for layer in layers ] 
            }
        return simplejson.dumps(map)

    def get_absolute_url(self):
        return '/maps/%i' % self.id
        
    class Meta:
        # custom permissions, 
        # change and delete are standard in django
        permissions = (('view_map', 'Can view'), 
                       ('change_map_permissions', "Can change permissions"), )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ  = 'map_readonly'
    LEVEL_WRITE = 'map_readwrite'
    LEVEL_ADMIN = 'map_admin'
    
    def set_default_permissions(self):
        self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_WRITE) 

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)    




class MapLayer(models.Model):
    name = models.CharField(max_length=200)
    styles = models.CharField(max_length=200)
    opacity = models.FloatField(default=1.0)
    format = models.CharField(max_length=200)
    transparent = models.BooleanField()
    ows_url = models.URLField()
    group = models.CharField(max_length=200,blank=True)
    stack_order = models.IntegerField()
    map = models.ForeignKey(Map, related_name="layer_set")

    def local(self): 
        layer = Layer.objects.filter(typename=self.name)
        if layer.count() == 0:
            return False
        else: 
            return True

    @property
    def local_link(self): 
        if self.local():
            layer = Layer.objects.get(typename=self.name)
            link = "<a href=\"%s\">%s</a>" % (layer.get_absolute_url(),self.name)
        else: 
            link = "<span>%s</span> " % self.name
        return link

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)

class Role(models.Model):
    """
    Roles are a generic way to create groups of permissions.
    """
    value = models.CharField('Role', choices= [(x, x) for x in ROLE_VALUES], max_length=255, unique=True)
    permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'), blank=True)

    def __unicode__(self):
        return self.get_value_display()


class ContactRole(models.Model):
    """
    ContactRole is an intermediate model to bind Contacts and Layers and apply roles.
    """
    contact = models.ForeignKey(Contact)
    layer = models.ForeignKey(Layer)
    role = models.ForeignKey(Role)

    def clean(self):
        """
        Make sure there is only one poc and author per layer
        """
        if (self.role == self.layer.poc_role) or (self.role == self.layer.metadata_author_role):
            if self.layer.contacts.filter(contactrole__role=self.role).count() > 0:
                 raise ValidationError('There can be only one %s for a given layer' % self.role)
        if self.contact.user is None:
            # verify that any unbound contact is only associated to one layer
            bounds = ContactRole.objects.filter(contact=self.contact).count()
            if bounds > 1:
                raise ValidationError('There can be one and only one layer linked to an unbound contact' % self.role)
            elif bounds == 1:
                # verify that if there was one already, it corresponds to this instace
                if ContactRole.objects.filter(contact=self.contact).get().id != self.id:
                    raise ValidationError('There can be one and only one layer linked to an unbound contact' % self.role)

    class Meta:
        unique_together = (("contact", "layer", "role"),)

def delete_layer(instance, sender, **kwargs): 
    """
    Removes the layer from GeoServer and GeoNetwork
    """
    instance.delete_from_geoserver()
    instance.delete_from_geonetwork()

def post_save_layer(instance, sender, **kwargs):
    instance._autopopulate()
    instance.save_to_geoserver()

    if kwargs['created']:
        instance._populate_from_gs()

    instance.save_to_geonetwork()

    if kwargs['created']:
        instance._populate_from_gn()
        instance.save(force_update=True)

signals.pre_delete.connect(delete_layer, sender=Layer)
signals.post_save.connect(post_save_layer, sender=Layer)
