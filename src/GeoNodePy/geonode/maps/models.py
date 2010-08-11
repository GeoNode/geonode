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
from django.utils.html import escape
import httplib2
import simplejson
import urllib
import uuid
import datetime
from django.contrib.auth.models import User, Permission
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from StringIO import StringIO
from xml.etree.ElementTree import parse

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

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.organization)


def get_csw():
    csw_url = "%ssrv/en/csw" % settings.GEONETWORK_BASE_URL
    csw = CatalogueServiceWeb(csw_url);
    return csw

_viewer_projection_lookup = {
    "EPSG:900913": {
        "maxResolution": 156543.0339,
        "units": "m",
        "maxExtent": [-20037508.34,-20037508.34,20037508.34,20037508.34],
    },
    "EPSG:4326": {
        "max_resolution": (180 - (-180)) / 256,
        "units": "degrees",
        "maxExtent": [-180, -90, 180, 90]
    }
}

def _get_viewer_projection_info(srid):
    # TODO: Look up projection details in EPSG database
    return _viewer_projection_lookup.get(srid, {})

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
            raise RuntimeError('GeoNode needs at least one admin/superuser set')
        
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
        elif self.resource.resource_type == "coverage":
            try:
                client = httplib2.Http()
                description_url = settings.GEOSERVER_BASE_URL + "wcs?" + urllib.urlencode({
                        "service": "WCS",
                        "version": "1.0.0",
                        "request": "DescribeCoverage",
                        "coverages": self.typename
                    })
                response, content = client.request(description_url)
                doc = parse(StringIO(content))
                extent = doc.find("//%(gml)slimits/%(gml)sGridEnvelope" % {"gml": "{http://www.opengis.net/gml}"})
                low = extent.find("{http://www.opengis.net/gml}low").text.split()
                high = extent.find("{http://www.opengis.net/gml}high").text.split()
                w, h = [int(h) - int(l) for (h, l) in zip(high, low)]

                def wcs_link(mime):
                    return settings.GEOSERVER_BASE_URL + "wcs?" + urllib.urlencode({
                        "service": "WCS",
                        "version": "1.0.0",
                        "request": "GetCoverage",
                        "CRS": "EPSG:4326",
                        "height": h,
                        "width": w,
                        "coverage": self.typename,
                        "bbox": bbox_string,
                        "format": mime
                    })

                types = [("tiff", "GeoTIFF", "geotiff")]
                links.extend([(ext, name, wcs_link(mime)) for (ext, name, mime) in types])
            except Exception, e:
                # if something is wrong with WCS we probably don't want to link
                # to it anyway
                pass 

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
            ("jpg", _("JPEG"), "image/jpeg"),
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
        if self.resource is None:
            return
        if hasattr(self, "_resource_cache"):
            self.resource.title = self.title
            self.resource.abstract = self.abstract
            self.resource.name= self.name
            Layer.objects.gs_catalog.save(self._resource_cache)
        if hasattr(self, "_publishing_cache"):
            Layer.objects.gs_catalog.save(self._publishing_cache)

    def  _populate_from_gs(self):
        gs_resource = Layer.objects.gs_catalog.get_resource(self.name)
        if gs_resource is None:
            return
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
        if meta is None:
            return
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
    """
    A Map aggregates several layers together and annotates them with a viewport
    configuration.
    """

    title = models.CharField(max_length=200)
    """
    A display name suitable for search results and page headers
    """

    abstract = models.CharField(max_length=200)
    """
    A longer description of the themes in the map.
    """

    # viewer configuration
    zoom = models.IntegerField()
    """
    The zoom level to use when initially loading this map.  Zoom levels start
    at 0 (most zoomed out) and each increment doubles the resolution.
    """

    projection = models.CharField(max_length=32)
    """
    The projection used for this map.  This is stored as a string with the
    projection's SRID.
    """

    center_x = models.FloatField()
    """
    The x coordinate to center on when loading this map.  Its interpretation
    depends on the projection.
    """

    center_y = models.FloatField()
    """
    The y coordinate to center on when loading this map.  Its interpretation
    depends on the projection.
    """

    owner = models.ForeignKey(User, blank=True, null=True)
    """
    The user that created/owns this map.
    """

    last_modified = models.DateTimeField(auto_now_add=True)
    """
    The last time the map was modified.
    """

    def __unicode__(self):
        return '%s by %s' % (self.title, (self.owner.username if self.owner else "<Anonymous>"))

    @property
    def center(self):
        """
        A handy shortcut for the center_x and center_y properties as a tuple
        (read only)
        """
        return (self.center_x, self.center_y)

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

    def viewer_json(self, *added_layers):
        """
        Convert this map to a nested dictionary structure matching the JSON
        configuration for GXP Viewers.

        The ``added_layers`` parameter list allows a list of extra MapLayer
        instances to append to the Map's layer list when generating the
        configuration. These are not persisted; if you want to add layers you
        should use ``.layer_set.create()``.
        """
        layers = list(self.layer_set.all()) + list(added_layers) #implicitly sorted by stack_order
        server_lookup = {}
        sources = dict()

        def uniqify(seq):
            """
            get a list of unique items from the input sequence.
            
            This relies only on equality tests, so you can use it on most
            things.  If you have a sequence of hashables, list(set(seq)) is
            better.
            """
            results = []
            for x in seq:
                if x not in results: results.append(x)
            return results

        configs = [l.source_config() for l in layers]
        configs.append({"ptype":"gx_wmssource", "url": settings.GEOSERVER_BASE_URL + "wms"})

        i = 0
        for source in uniqify(configs):
            while str(i) in sources: i = i + 1
            sources[str(i)] = source 
            server_lookup[simplejson.dumps(source)] = str(i)

        def source_lookup(source):
            for k, v in sources.iteritems():
                if v == source: return k
            return None

        def layer_config(l):
            cfg = l.layer_config()
            source = source_lookup(l.source_config())
            if source: cfg["source"] = source
            return cfg

        config = {
            'id': self.id,
            'about': {
                'title':    self.title,
                'abstract': self.abstract
            },
            'defaultSourceType': "gx_wmssource",
            'sources': sources,
            'map': {
                'layers': [layer_config(l) for l in layers],
                'center': [self.center_x, self.center_y],
                'projection': self.projection,
                'zoom': self.zoom
            }
        }

        config["map"].update(_get_viewer_projection_info(self.projection))

        return config

    def update_from_viewer(self, conf):
        """
        Update this Map's details by parsing a JSON object as produced by
        a GXP Viewer.  
        
        This method automatically persists to the database!
        """
        if isinstance(conf, basestring):
            conf = simplejson.loads(conf)

        self.title = conf['about']['title']
        self.abstract = conf['about']['abstract']

        self.zoom = conf['map']['zoom']

        self.center_x = conf['map']['center'][0]
        self.center_y = conf['map']['center'][1]

        self.projection = conf['map']['projection']

        self.featured = conf['about'].get('featured', False)

        def source_for(layer):
            return conf["sources"][layer["source"]]

        layers = [l for l in conf["map"]["layers"]]
        
        for layer in self.layer_set.all():
            layer.delete()

        for ordering, layer in enumerate(layers):
            self.layer_set.add(
                self.layer_set.from_viewer_config(
                    self, layer, source_for(layer), ordering
            ))
        self.save()

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



class MapLayerManager(models.Manager):
    def from_viewer_config(self, map, layer, source, ordering):
        """
        Parse a MapLayer object out of a parsed layer configuration from a GXP
        viewer.

        ``map`` is the Map instance to associate with the new layer
        ``layer`` is the parsed dict for the layer
        ``source`` is the parsed dict for the layer's source
        ``ordering`` is the index of the layer within the map's layer list
        """
        layer_cfg = dict(layer)
        for k in ["format", "name", "opacity", "styles", "transparent",
                  "fixed", "group", "visibility", "title", "source"]:
            if k in layer_cfg: del layer_cfg[k]

        source_cfg = dict(source)
        for k in ["url", "projection"]:
            if k in source_cfg: del source_cfg[k]

        return self.model(
            map = map,
            stack_order = ordering,
            format = layer.get("format", None),
            name = layer.get("name", None),
            opacity = layer.get("opacity", 1),
            styles = layer.get("styles", None),
            transparent = layer.get("transparent", False),
            fixed = layer.get("fixed", False),
            group = layer.get('group', None),
            visibility = layer.get("visibility", True),
            ows_url = source.get("url", None),
            layer_params = simplejson.dumps(layer_cfg),
            source_params = simplejson.dumps(source_cfg)
        )

class MapLayer(models.Model):
    """
    The MapLayer model represents a layer included in a map.  This doesn't just
    identify the dataset, but also extra options such as which style to load
    and the file format to use for image tiles.
    """

    objects = MapLayerManager()
    """
    see :class:`geonode.maps.models.MapLayerManager`
    """

    map = models.ForeignKey(Map, related_name="layer_set")
    """
    The map containing this layer
    """

    stack_order = models.IntegerField()
    """
    The z-index of this layer in the map; layers with a higher stack_order will
    be drawn on top of others.
    """

    format = models.CharField(null=True,max_length=200)
    """
    The mimetype of the image format to use for tiles (image/png, image/jpeg,
    image/gif...)
    """

    name = models.CharField(null=True,max_length=200)
    """
    The name of the layer to load.

    The interpretation of this name depends on the source of the layer (Google
    has a fixed set of names, WMS services publish a list of available layers
    in their capabilities documents, etc.)
    """

    opacity = models.FloatField(default=1.0)
    """
    The opacity with which to render this layer, on a scale from 0 to 1.
    """

    styles = models.CharField(null=True,max_length=200)
    """
    The name of the style to use for this layer (only useful for WMS layers.)
    """

    transparent = models.BooleanField()
    """
    A boolean value, true if we should request tiles with a transparent background.
    """

    fixed = models.BooleanField(default=False)
    """
    A boolean value, true if we should prevent the user from dragging and
    dropping this layer in the layer chooser.
    """

    group = models.CharField(null=True,max_length=200)
    """
    A group label to apply to this layer.  This affects the hierarchy displayed
    in the map viewer's layer tree.
    """

    visibility = models.BooleanField(default=True)
    """
    A boolean value, true if this layer should be visible when the map loads.
    """

    ows_url = models.URLField(null=True)
    """
    The URL of the OWS service providing this layer, if any exists.
    """

    layer_params = models.CharField(max_length=1024)
    """
    A JSON-encoded dictionary of arbitrary parameters for the layer itself when
    passed to the GXP viewer.

    If this dictionary conflicts with options that are stored in other fields
    (such as format, styles, etc.) then the fields override.
    """

    source_params = models.CharField(max_length=1024)
    """
    A JSON-encoded dictionary of arbitrary parameters for the GXP layer source
    configuration for this layer.

    If this dictionary conflicts with options that are stored in other fields
    (such as ows_url) then the fields override.
    """
    
    def local(self): 
        layer = Layer.objects.filter(typename=self.name)
        if layer.count() == 0:
            return False
        else: 
            return True
 
    def source_config(self):
        """
        Generate a dict that can be serialized to a GXP layer source
        configuration suitable for loading this layer.
        """
        try:
            cfg = simplejson.loads(self.source_params)
        except:
            cfg = dict(ptype = "gx_wmssource")

        if self.ows_url: cfg["url"] = self.ows_url

        return cfg

    def layer_config(self):
        """
        Generate a dict that can be serialized to a GXP layer configuration
        suitable for loading this layer.

        The "source" property will be left unset; the layer is not aware of the
        name assigned to its source plugin.  See
        :method:`geonode.maps.models.Map.viewer_json` for an example of
        generating a full map configuration.
        """
        try:
            cfg = simplejson.loads(self.layer_params)
        except: 
            cfg = dict()

        if self.format: cfg['format'] = self.format
        if self.name: cfg["name"] = self.name
        if self.opacity: cfg['opacity'] = self.opacity
        if self.styles: cfg['styles'] = self.styles
        if self.transparent: cfg['transparent'] = True

        cfg["fixed"] = self.fixed
        if self.group: cfg["group"] = self.group
        cfg["visibility"] = self.visibility

        return cfg


    @property
    def local_link(self): 
        if self.local():
            layer = Layer.objects.get(typename=self.name)
            link = "<a href=\"%s\">%s</a>" % (layer.get_absolute_url(),layer.title)
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
