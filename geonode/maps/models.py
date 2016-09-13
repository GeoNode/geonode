# -*- coding: UTF-8 -*-
import threading
from django.conf import settings
from django.db import models
from geonode.maps.owslib_csw import CatalogueServiceWeb
from geoserver.catalog import Catalog
from geonode.core.models import PermissionLevelMixin
from geonode.core.models import AUTHENTICATED_USERS, ANONYMOUS_USERS, CUSTOM_GROUP_USERS
from geonode.geonetwork import Catalog as GeoNetwork
from django.db.models import signals
from taggit.managers import TaggableManager
from django.utils import simplejson as json
from django.utils.safestring import mark_safe

import httplib2
import urllib
from urlparse import urlparse
import uuid
from datetime import datetime
from django.contrib.auth.models import User, Permission
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from lxml import etree
from geonode.maps.gs_helpers import cascading_delete, get_postgis_bbox
import logging
from geonode.maps.encode import num_encode
from django.core.cache import cache
import sys
import re
from geonode.maps.encode import despam, XssCleaner
from geonode.flexidates import FlexiDateField, FlexiDateFormField


logger = logging.getLogger("geonode.maps.models")


ows_sub = re.compile(r"[&\?]+SERVICE=WMS|[&\?]+REQUEST=GetCapabilities", re.IGNORECASE)


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


KEYWORD_REGIONS= (
    ('GLO', _('Global')),
    ('NAM', _('North America')),
    ('CAM',_('Central America')),
    ('SAM',_('South America')),
    ('EUR',_('Europe')),
    ('ASI',_('Asia')),
    ('SEA',_('Southeast Asia')),
    ('CTA',_('Central Asia')),
    ('SAS',_('South Asia')),
    ('AFR',_('Africa')),
    ('NAF',_('North Africa')),
    ('EAF',_('East Africa')),
    ('WAF',_('West Africa')),
    ('SAF',_('South Africa')),
    ('MES',_('Middle East')),
    ('ANT',_('Antarctica')),
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
    ('chi', 'Chinese'),
    ('cos', 'Corsican'),
    ('dan', 'Danish'),
    ('dzo', 'Dzongkha'),
    ('eng', 'English'),
    ('fra', 'French'),
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
    ('spa', 'Spanish'),
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


CHARSETS = [
    ['', 'None/Unknown'],
    ['UTF-8', 'UTF-8/Unicode'],
    ['ISO-8859-1', 'Latin1/ISO-8859-1'],
    ['ISO-8859-2', 'Latin2/ISO-8859-2'],
    ['ISO-8859-3', 'Latin3/ISO-8859-3'],
    ['ISO-8859-4', 'Latin4/ISO-8859-4'],
    ['ISO-8859-5', 'Latin5/ISO-8859-5'],
    ['ISO-8859-6', 'Latin6/ISO-8859-6'],
    ['ISO-8859-7', 'Latin7/ISO-8859-7'],
    ['ISO-8859-8', 'Latin8/ISO-8859-8'],
    ['ISO-8859-9', 'Latin9/ISO-8859-9'],
    ['ISO-8859-10','Latin10/ISO-8859-10'],
    ['ISO-8859-13','Latin13/ISO-8859-13'],
    ['ISO-8859-14','Latin14/ISO-8859-14'],
    ['ISO8859-15','Latin15/ISO-8859-15'],
    ['Big5', 'BIG5'],
    ['EUC-JP','EUC-JP'],
    ['EUC-KR','EUC-KR'],
    ['GBK','GBK'],
    ['GB18030','GB18030'],
    ['Shift_JIS','Shift_JIS'],
    ['KOI8-R','KOI8-R'],
    ['KOI8-U','KOI8-U'],
    ['windows-874', 'Windows CP874'],
    ['windows-1250', 'Windows CP1250'],
    ['windows-1251', 'Windows CP1251'],
    ['windows-1252', 'Windows CP1252'],
    ['windows-1253', 'Windows CP1253'],
    ['windows-1254', 'Windows CP1254'],
    ['windows-1255', 'Windows CP1255'],
    ['windows-1256', 'Windows CP1256'],
    ['windows-1257', 'Windows CP1257'],
    ['windows-1258', 'Windows CP1258']
]


UPDATE_FREQUENCIES = [
    ['annually', _('Annually')],
    ['asNeeded', _('As Needed')],
    ['biannually', _('Biannually')],
    ['continual', _('Continual')],
    ['daily', _('Daily')],
    ['fortnightly', _('Fortnightly')],
    ['irregular', _('Irregular')],
    ['monthly', _('Monthly')],
    ['notPlanned', _('Not Planned')],
    ['quarterly', _('Quarterly')],
    ['unknown', _('Unknown')],
    ['weekly', _('Weekly')]
]

CONSTRAINT_OPTIONS = [
    # Shortcuts added for convenience in Open Data cases.
    ['Public Domain Dedication and License (PDDL)',_('Public Domain Dedication and License (PDDL)')],
    ['Attribution License (ODC-By)', _('Attribution License (ODC-By)')],
    ['Open Database License (ODC-ODbL)',_('Open Database License (ODC-ODbL)')],
    ['CC-BY-SA',_('CC-BY-SA')],

    # ISO standard constraint options.
    ['copyright', _('Copyright')],
    ['intellectualPropertyRights', _('Intellectual Porperty Rights')],
    ['license', _('License')],
    ['otherRestrictions', _('Other Restrictions')],
    ['patent', _('patent')],
    ['patentPending', _('Patent Pending')],
    ['restricted', _('Restricted')],
    ['trademark', _('Trademark')],
    ['public', _('Public')],
    ['no restrictions', _('No Restrictions')]
]

SPATIAL_REPRESENTATION_TYPES = [
    ['grid', _('Grid')],
    ['steroModel', _('Stereo Model')],
    ['textTable', _('Text Table')],
    ['tin', 'TIN'],
    ['vector', 'Vector']
]


CONTACT_FIELDS = [
    ["name", _("Name")],
    ["organization", _("Organization")],
    ["position", _("Position")],
    ["voice", _("Voice")],
    ["facsimile", _("Fax")],
    ["delivery_point", _("Delivery Point")],
    ["city", _("City")],
    ["administrative_area", _("Administrative Area")],
    ["postal_code", _("Postal Code")],
    ["country", _("Country")],
    ["email", _("Email")],
    ["role", _("Role")]
]

DEFAULT_SUPPLEMENTAL_INFORMATION=''

DEFAULT_CONTENT=_(
    '<h3>The Harvard WorldMap Project</h3>\
  <p>WorldMap is an open source web mapping system that is currently\
  under construction. It is built to assist academic research and\
  teaching as well as the general public and supports discovery,\
  investigation, analysis, visualization, communication and archiving\
  of multi-disciplinary, multi-source and multi-format data,\
  organized spatially and temporally.</p>\
  <p>The first instance of WorldMap, focused on the continent of\
  Africa, is called AfricaMap. Since its beta release in November of\
  2008, the framework has been implemented in several geographic\
  locations with different research foci, including metro Boston,\
  East Asia, Vermont, Harvard Forest and the city of Paris. These web\
  mapping applications are used in courses as well as by individual\
  researchers.</p>\
  <h3>Introduction to the WorldMap Project</h3>\
  <p>WorldMap solves the problem of discovering where things happen.\
  It draws together an array of public maps and scholarly data to\
  create a common source where users can:</p>\
  <ol>\
  <li>Interact with the best available public data for a\
  city/region/continent</li>\
  <li>See the whole of that area yet also zoom in to particular\
  places</li>\
  <li>Accumulate both contemporary and historical data supplied by\
  researchers and make it permanently accessible online</li>\
  <li>Work collaboratively across disciplines and organizations with\
  spatial information in an online environment</li>\
  </ol>\
  <p>The WorldMap project aims to accomplish these goals in stages,\
  with public and private support. It draws on the basic insight of\
  geographic information systems that spatiotemporal data becomes\
  more meaningful as more "layers" are added, and makes use of tiling\
  and indexing approaches to facilitate rapid search and\
  visualization of large volumes of disparate data.</p>\
  <p>WorldMap aims to augment existing initiatives for globally\
  sharing spatial data and technology such as <a target="_blank" href="http://www.gsdi.org/">GSDI</a> (Global Spatial Data\
  Infrastructure).WorldMap makes use of <a target="_blank" href="http://www.opengeospatial.org/">OGC</a> (Open Geospatial\
  Consortium) compliant web services such as <a target="_blank" href="http://en.wikipedia.org/wiki/Web_Map_Service">WMS</a> (Web\
  Map Service), emerging open standards such as <a target="_blank" href="http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification">WMS-C</a>\
  (cached WMS), and standards-based metadata formats, to enable\
  WorldMap data layers to be inserted into existing data\
  infrastructures.&nbsp;<br>\
  <br>\
  All WorldMap source code will be made available as <a target="_blank" href="http://www.opensource.org/">Open Source</a> for others to use\
  and improve upon.</p>'
)


class GeoNodeException(Exception):
    pass


#class ResourceBase(models.Model):
#    pass

class Contact(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    name = models.CharField(_('Individual Name'), max_length=255, blank=True, null=True)
    organization = models.CharField(_('Organization Name'), max_length=255, blank=True, null=True)
    position = models.CharField(_('Position Name'), max_length=255, blank=True, null=True)
    voice = models.CharField(_('Phone'), max_length=255, blank=True, null=True)
    fax = models.CharField(_('Fax'),  max_length=255, blank=True, null=True)
    delivery = models.CharField(_('Address'), max_length=255, blank=True, null=True)
    city = models.CharField(_('City'), max_length=255, blank=True, null=True)
    area = models.CharField(_('State/Province'), max_length=255, blank=True, null=True)
    zipcode = models.CharField(_('Postal Code'), max_length=255, blank=True, null=True)
    country = models.CharField(choices=COUNTRIES, max_length=3, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=False)
    display_email = models.BooleanField(_('Display my email address on my profile'), blank=False, default=False, null=False)
    is_org_member = models.BooleanField(_('Affiliated with Harvard'), blank=True, null=False, default=False)
    member_expiration_dt = models.DateField(_('Harvard affiliation expires on: '), blank=False, null=False, default=datetime.today())
    keywords = TaggableManager(_('keywords'), help_text=_("A space or comma-separated list of keywords"), blank=True)
    is_certifier = models.BooleanField(_('Allowed to certify maps & layers'), blank=False, null=False, default=False)

    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the object was created.
    """

    last_modified = models.DateTimeField(auto_now=True)
    """
    The last time the object was modified.
    """


    def clean(self):
        # the specification says that either name or organization should be provided
        valid_name = (self.name != None and self.name != '')
        valid_organization = (self.organization != None and self.organization !='')
        if not (valid_name or valid_organization):
            raise ValidationError(_('Either name or organization should be provided'))
        if self.email and User.objects.filter(email=self.email).exclude(username=self.user.username if self.user else '').count():
            raise ValidationError(_('The email address is already registered.'))

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)

    def __unicode__(self):
        return u"%s (%s)" % (self.name if self.name else self.user.username, self.organization)

    def username(self):
        return u"%s" % (self.name if self.name else self.user.username)

def create_user_profile(sender, instance, created, **kwargs):
    profile, created = Contact.objects.get_or_create(user=instance, defaults={'name': instance.username})

signals.post_save.connect(create_user_profile, sender=User)


_viewer_projection_lookup = {
    "EPSG:900913": {
        "maxResolution": 156543.03390625,
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
    #TODO: Look up projection details in EPSG database
    return _viewer_projection_lookup.get(srid, {})

_wms = None
_csw = None
_user, _password = settings.GEOSERVER_CREDENTIALS

#def get_wms():
#    global _wms
#    wms_url = settings.GEOSERVER_BASE_URL + "wms?request=GetCapabilities&version=1.1.0"
#    netloc = urlparse(wms_url).netloc
#    http = httplib2.Http()
#    http.add_credentials(_user, _password)
#    http.authorizations.append(
#        httplib2.BasicAuthentication(
#            (_user, _password),
#                netloc,
#                wms_url,
#                {},
#                None,
#                None,
#                http
#            )
#        )
#    body = http.request(wms_url)[1]
#    _wms = WebMapService(wms_url, xml=body)

def get_csw():
    global _csw
    csw_url = "%ssrv/en/csw" % settings.GEONETWORK_BASE_URL
    _csw = CatalogueServiceWeb(csw_url)
    return _csw

class LayerManager(models.Manager):

    def __init__(self):
        models.Manager.__init__(self)
        url = "%srest" % settings.GEOSERVER_BASE_URL
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

        contact = Contact.objects.get_or_create(user=superusers[0],
            defaults={"name": "Geonode Admin"})[0]
        return contact

    def default_poc(self):
        return self.admin_contact()

    def default_metadata_author(self):
        return self.admin_contact()

    def drop_incomplete_layers(self, ignore_errors=True, verbosity=1, console=sys.stdout, owner=None, max_views=0):
        bad_layers = Layer.objects.filter(topic_category_id__isnull=True).filter(created_dttm__lt=datetime.today)  \
            .exclude(owner__isnull=True).exclude(owner_id=1)
        lc = 0
        for layer in bad_layers:
            maplayers = MapLayer.objects.filter(name=layer.typename)
            if maplayers.count() == 0:
                stats = LayerStats.objects.filter(layer=layer)
                if len(stats) == 0 or stats[0].visits <= max_views:
                    print >> console, "Delete %s" % layer.typename
                    lc+=1
                else:
                    print >> console, "Skip %s, has been viewed more than %d times" % (layer.typename, max_views)
            else:
                print >> console, "Skip %s, has been included in a map" % (layer.typename)
        print >> console, "%d layers deleted" % lc


    def slurp(self, ignore_errors=True, verbosity=1, console=sys.stdout, owner=None, new_only=False, lnames=None, workspace=None):
        """Configure the layers available in GeoServer in GeoNode.

           It returns a list of dictionaries with the name of the layer,
           the result of the operation and the errors and traceback if it failed.
        """
        if verbosity > 1:
            print >> console, "Inspecting the available layers in GeoServer ..."
        cat = self.gs_catalog
        resources = []
        if workspace is not None:
            print >> console, "Workspace is  %s" % workspace
            workspace = cat.get_workspace(workspace)
            resources = cat.get_resources(workspace=workspace)
        output = []

        # check lnames
        if lnames is not None:
            for l in lnames:
                if verbosity > 1:
                    print >> console, "Getting  %s" % l
                resource = cat.get_resource(l)
            if resource:
                resources.append(resource)
        else:
            if verbosity > 1:
                print >> console, "Getting  all resources"
            resources = cat.get_resources()

        number = len(resources)

        if verbosity > 1:
            msg =  "Found %d layers, starting processing" % number
            print >> console, msg

        for i, resource in enumerate(resources):
            name = resource.name
            store = resource.store
            workspace = store.workspace

            if new_only and Layer.objects.filter(name=name).exists():
                continue
            elif lnames is not None and name not in lnames:
                continue

            try:
                layer, created = Layer.objects.get_or_create(name=name, defaults = {
                    "workspace": workspace.name,
                    "store": store.name,
                    "storeType": store.resource_type,
                    "typename": "%s:%s" % (workspace.name, resource.name),
                    "title": resource.title or 'No title provided',
                    "abstract": resource.abstract or 'No abstract provided',
                    "owner": owner,
                    "uuid": str(uuid.uuid4())
                })
                if layer is not None and layer.topic_category is None:
                    # we need a default category, otherwise metadata are not generated
                    default_category = LayerCategory.objects.get(name='boundaries')
                    layer.topic_category = default_category
                    layer.save()
                if layer is not None and layer.bbox is None:
                    layer._populate_from_gs()
                layer.save()
            except Exception, e:
                if ignore_errors:
                    status = 'failed'
                    exception_type, error, traceback = sys.exc_info()
                else:
                    if verbosity > 0:
                        msg = "Stopping process because --ignore-errors was not set and an error was found."
                        print >> sys.stderr, msg
                    raise Exception('Failed to process %s' % resource.name, e), None, sys.exc_info()[2]
            else:
                if created:
                    layer.set_default_permissions()
                    status = 'created'
                else:
                    status = 'updated'

                #Create layer attributes if they don't already exist
                try:
                    if layer.attribute_names is not None:
                        iter = 1
                        for field, ftype in layer.attribute_names.iteritems():
                            if field is not None:
                                la, created = LayerAttribute.objects.get_or_create(layer=layer, attribute=field, attribute_type=ftype)
                                if created:
                                    la.attribute_label = field
                                    la.searchable = (ftype == "xsd:string")
                                    la.display_order = iter
                                    la.save()
                                    msg = ("Created [%s] attribute for [%s]", field, layer.name)
                                    iter += 1
                                    print >> console, msg
                except Exception, e:
                    msg = ("Could not create attributes for [%s] : [%s]", layer.name, str(e))
                    print >> console, msg
                finally:
                    pass

            msg = "[%s] Layer %s (%d/%d)" % (status, name, i+1, number)
            info = {'name': name, 'status': status}
            if status == 'failed':
                info['traceback'] = traceback
                info['exception_type'] = exception_type
                info['error'] = error
            output.append(info)
            if verbosity > 0:
                print >> console, msg
        return output


    def update_bboxes(self):
        for layer in Layer.objects.all():
            logger.debug('Process %s', layer.name)
            if layer.srs is None or layer.llbbox is None or layer.bbox is None:
                logger.debug('Process %s', layer.name)
                layer._populate_from_gs()
                layer.save()

    def update_stores(self):
        cat = self.gs_catalog
        for layer in Layer.objects.all():
            logger.debug('Process %s', layer.name)
            resource = cat.get_resource(layer.name)
            if resource:
                store = resource.store
                if layer.store != store.name:
                    logger.debug('Change store name of %s from %s to %s', layer.name, layer.store, store.name)
                    layer.store = store.name
                    layer.save()


class LayerCategory(models.Model):
    name = models.CharField(_('Category Name'), max_length=255, blank=True, null=True, unique=True)
    title = models.CharField(_('Category Title'), max_length=255, blank=True, null=True, unique=True)
    description = models.TextField(_('Category Description'), blank=True, null=True)
    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the object was created.
    """

    last_modified = models.DateTimeField(auto_now=True)
    """
    The last time the object was modified.
    """

    def __str__(self):
        return "%s" % self.name

    class Meta:
        verbose_name_plural = 'Layer Categories'


class Layer(models.Model, PermissionLevelMixin):
#class Layer(ResourceBase, PermissionLevelMixin):
    """
    Layer Object loosely based on ISO 19115:2003
    """

    VALID_DATE_TYPES = [(x.lower(), _(x)) for x in ['Creation', 'Publication', 'Revision']]

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
    title = models.CharField(_('title'), max_length=255)
    date = models.DateTimeField(_('date'), default = datetime.now) # passing the method itself, not the result

    date_type = models.CharField(_('date type'), max_length=255, choices=VALID_DATE_TYPES, default='publication')

    edition = models.CharField(_('edition'), max_length=255, blank=True, null=True)
    abstract = models.TextField(_('abstract'), blank=False)
    purpose = models.TextField(_('purpose'), null=True, blank=True)
    maintenance_frequency = models.CharField(_('maintenance frequency'), max_length=255, choices=UPDATE_FREQUENCIES, blank=True, null=True)

    # section 2
    # see poc property definition below

    # section 3
    keywords = TaggableManager(_('keywords'), help_text=_("A space or comma-separated list of keywords"), blank=True)
    keywords_region = models.CharField(_('keywords region'), max_length=3, choices=KEYWORD_REGIONS + COUNTRIES, default = 'GLO')
    constraints_use = models.CharField(_('constraints use'), max_length=255, choices=CONSTRAINT_OPTIONS, default='copyright')
    constraints_other = models.TextField(_('constraints other'), blank=True, null=True)
    spatial_representation_type = models.CharField(_('spatial representation type'), max_length=255, choices=SPATIAL_REPRESENTATION_TYPES, blank=True, null=True)

    # Section 4
    language = models.CharField(_('language'), max_length=3, choices=ALL_LANGUAGES, default='eng')
    topic_category = models.ForeignKey(LayerCategory, blank=True, null=True)

    # Section 5
    temporal_extent_start = models.CharField(_('temporal extent start'), max_length=24, blank=True, null=True)
    temporal_extent_end = models.CharField(_('temporal extent end'), max_length=24, blank=True, null=True)
    geographic_bounding_box = models.TextField(_('geographic bounding box'))
    supplemental_information = models.TextField(_('supplemental information'), blank=True, null=True, default='')

    # Section 6
    distribution_url = models.TextField(_('distribution URL'), blank=True, null=True)
    distribution_description = models.TextField(_('distribution description'), blank=True, null=True)

    # WMS attributes
    srs = models.CharField(_('SRS'), max_length=24, blank=True, null=True, default="EPSG:4326")
    bbox  = models.TextField(_('bbox'), blank=True, null=True)
    llbbox = models.TextField(_('llbbox'), blank=True, null=True)


    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the object was created.
    """
    last_modified = models.DateTimeField(auto_now=True)
    """
    The last time the object was modified.
    """

    downloadable = models.BooleanField(_('Downloadable?'), blank=False, null=False, default=True)
    """
    Is the layer downloadable?
    """

    in_gazetteer = models.BooleanField(_('In Gazetteer?'), blank=False, null=False, default=False)
    """
    Is the layer in the gazetteer?
    """

    gazetteer_project = models.CharField(_("Gazetteer Project"), max_length=128, blank=True, null=True)
    """
    Gazetteer project that the layer is associated with
    """

    # Section 8
    data_quality_statement = models.TextField(_('data quality statement'), blank=True, null=True)

    # Section 9
    # see metadata_author property definition below

    # join target: available only for layers within the DATAVERSE_DB
    def add_as_join_target(self):
        if not self.id:
            return 'n/a'
        if self.store != settings.DB_DATAVERSE_NAME:
            return 'n/a'
        admin_url = reverse('admin:datatables_jointarget_add', args=())
        add_as_target_link = '%s?layer=%s' % (admin_url, self.id)
        return '<a href="%s">Add as Join Target</a>' % (add_as_target_link)
    add_as_join_target.allow_tags = True

    def llbbox_coords(self):
        try:
            return [float(n) for n in re.findall('[0-9\.\-]+', self.llbbox)]
        except:
            return [-180.0,-90.0,180.0,90.0]

    def bbox_coords(self):
        try:
            return [float(n) for n in re.findall('[0-9\.\-]+', self.bbox)]
        except:
            return self.llbbox_coords

    def download_links(self):
        """Returns a list of (mimetype, URL) tuples for downloads of this data
        in various formats."""

        if not self.downloadable:
            return None

        bbox = self.llbbox_coords()

        dx = float(min(180,bbox[2])) - float(max(-180,(bbox[0])))
        dy = float(min(90,bbox[3])) - float(max(-90,bbox[1]))

        dataAspect = 1 if dy == 0 else dx / dy

        height = 550
        width = int(height * dataAspect)

        # bbox: this.adjustBounds(widthAdjust, heightAdjust, values.llbbox).toString(),

        srs = 'EPSG:4326' # bbox[4] might be None
        bbox_string = ",".join([str(bbox[0]), str(bbox[1]), str(bbox[2]), str(bbox[3])])

        links = []

        if self.resource.resource_type == "featureType":
            def wfs_link(mime,extra_params,ext):
                return settings.SITEURL + "download/wfs/" + str(self.id) + "/" + ext + "?" + urllib.urlencode({
                    'service': 'WFS',
                    'version': '1.0.0',
                    'request': 'GetFeature',
                    'typename': self.typename,
                    'outputFormat': mime,
                    'format_options': 'charset:UTF-8' #TODO: make this a settings property?
                })

            types = [
                ("zip", _("Zipped Shapefile"), "SHAPE-ZIP", {'format_options': 'charset:UTF-8'}),
                ("gml", _("GML 2.0"), "gml2", {}),
                ("gml", _("GML 3.1.1"), "text/xml; subtype=gml/3.1.1", {}),
                ("csv", _("CSV"), "csv", {}),
                ("xls", _("Excel"), "excel", {}),
                ("json", _("GeoJSON"), "json", {})
            ]
            links.extend((ext, name, wfs_link(mime, extra_params, ext)) for ext, name, mime, extra_params in types)
        elif self.resource.resource_type == "coverage":
            try:
                client = httplib2.Http()
                description_url = settings.SITEURL + "download/wcs/" + str(self.id)  + "/mime" + "?" + urllib.urlencode({
                    "service": "WCS",
                    "version": "1.0.0",
                    "request": "DescribeCoverage",
                    "coverage": self.typename
                })
                content = client.request(description_url)[1]
                doc = etree.fromstring(content)
                extent = doc.find(".//%(gml)slimits/%(gml)sGridEnvelope" % {"gml": "{http://www.opengis.net/gml}"})
                low = extent.find("{http://www.opengis.net/gml}low").text.split()
                high = extent.find("{http://www.opengis.net/gml}high").text.split()
                w, h = [int(h) - int(l) for (h, l) in zip(high, low)]

                def wcs_link(mime,ext):
                    return settings.SITEURL + "download/wcs/" + str(self.id) + "/" + ext + "?" + urllib.urlencode({
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

                types = [("tif", "GeoTIFF", "geotiff")]
                links.extend([(ext, name, wcs_link(mime,ext)) for (ext, name, mime) in types])
            except Exception, e:
                # if something is wrong with WCS we probably don't want to link
                # to it anyway
                # But at least this indicates a problem
                notiff = mark_safe("<del>GeoTIFF</del>")
                links.extend([("tiff",notiff,"#")])

        def wms_link(mime, ext):
            return settings.SITEURL + "download/wms/" + str(self.id) + "/" + ext + "?"  + urllib.urlencode({
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
            ("tiff", _("GeoTIFF"), "image/geotiff"),
            ("jpg", _("JPEG"), "image/jpeg"),
            ("pdf", _("PDF"), "application/pdf"),
            ("png", _("PNG"), "image/png")
        ]

        links.extend((ext, name, wms_link(mime,ext)) for ext, name, mime in types)

        kml_reflector_link_download = settings.SITEURL + "download/wms_kml/" + str(self.id) + "/kml" + "?"  + urllib.urlencode({
            'layers': self.typename,
            'mode': "download"
        })

        kml_reflector_link_view = settings.SITEURL + "download/wms_kml/" + str(self.id)  + "/kml" + "?" + urllib.urlencode({
            'layers': self.typename,
            'mode': "refresh"
        })

        links.append(("KML", _("KML"), kml_reflector_link_download))
        links.append(("KML", _("View in Google Earth"), kml_reflector_link_view))

        return links

    def verify(self):
        """Makes sure the state of the layer is consistent in GeoServer and GeoNetwork.
        """

        # Check the layer is in the GeoNetwork catalog and points back to get_absolute_url
        if(_csw is None): # Might need to re-cache, nothing equivalent to _wms.contents?
            get_csw()
        if _csw is not None:
            try:
                _csw.getrecordbyid([self.uuid])
                csw_layer = _csw.records.get(self.uuid)
            except:
                msg = "CSW Record Missing for layer [%s]" % self.typename
                raise GeoNodeException(msg)


    @property
    def attributes(self):
        """
        Used for table joins.  See geonode.contrib.datatables
        """
        return self.attribute_set.exclude(attribute='the_geom')


    def layer_attributes(self):
        attribute_fields = cache.get('layer_searchfields_' + self.typename)
        if attribute_fields is None:
            logger.debug("Create searchfields for %s", self.typename)
            attribute_fields = []
            attributes = self.attribute_set.filter(visible=True).order_by('display_order')
            for la in attributes:
                attribute_fields.append( {"id": la.attribute, "header": la.attribute_label, "searchable" : la.searchable})
            cache.add('layer_searchfields_' + self.typename, attribute_fields)
            logger.debug("cache created for layer %s", self.typename)
        return attribute_fields


    def attribute_config(self):
        #Get custom attribute sort order and labels if any
            cfg = {}
            visible_attributes =  self.attribute_set.visible()
            if (visible_attributes.count() > 0):
                cfg["getFeatureInfo"] = {
                    "fields":  [l.attribute for l in visible_attributes],
                    "propertyNames":   dict([(l.attribute,l.attribute_label) for l in visible_attributes])
                }
            return cfg

    def maps(self):
        """Return a list of all the maps that use this layer"""
        local_wms = "%swms" % settings.GEOSERVER_BASE_URL
        return set([layer.map for layer in MapLayer.objects.filter(ows_url=local_wms, name=self.typename).select_related()])

    #    def metadata(self):
    #        if (_wms is None) or (self.typename not in _wms.contents):
    #            get_wms()
    # wms_url = "%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL
    # netloc = urlparse(wms_url).netloc
    # http = httplib2.Http()
    # http.add_credentials(_user, _password)
    # http.authorizations.append(
    #     httplib2.BasicAuthentication(
    #         (_user, _password),
    #         netloc,
    #         wms_url,
    #         {},
    #         None,
    #         None,
    #         http
    #     )
    # )
    # response, body = http.request(wms_url)
    # _wms = WebMapService(wms_url, xml=body)
    #        return _wms[self.typename]

    def __setattr__(self, name, value):
        return super(Layer, self).__setattr__(name, value)

    def metadata_csw(self):
        global _csw
        if(_csw is None):
            _csw = get_csw()
        _csw.getrecordbyid([self.uuid], outputschema = 'http://www.isotc211.org/2005/gmd')
        return _csw.records.get(self.uuid)

    @property
    def attribute_names(self):
        from ordereddict import OrderedDict
        if self.resource.resource_type == "featureType":
            dft_url = settings.GEOSERVER_BASE_URL + "wfs?" + urllib.urlencode({
                "service": "wfs",
                "version": "1.0.0",
                "request": "DescribeFeatureType",
                "typename": self.typename
            })
            try:
                http = httplib2.Http()
                http.add_credentials(_user, _password)
                netloc = urlparse(dft_url).netloc
                http.authorizations.append(
                    httplib2.BasicAuthentication(
                        (_user, _password),
                        netloc,
                        dft_url,
                            {},
                        None,
                        None,
                        http
                    ))
                response, body = http.request(dft_url)
                doc = etree.fromstring(body)
                path = ".//{xsd}extension/{xsd}sequence/{xsd}element".format(xsd="{http://www.w3.org/2001/XMLSchema}")
                atts = OrderedDict({})
                for n in doc.findall(path):
                    logger.info("RESOURCE ATT %s", n.attrib["name"])
                    atts[n.attrib["name"]] = n.attrib["type"]
            except Exception:
                atts = {}
            return atts
        elif self.resource.resource_type == "coverage":
            dc_url = settings.GEOSERVER_BASE_URL + "wcs?" + urllib.urlencode({
                "service": "wcs",
                "version": "1.1.0",
                "request": "DescribeCoverage",
                "identifiers": self.typename
            })
            try:
                http = httplib2.Http()
                http.add_credentials(_user, _password)
                netloc = urlparse(dc_url).netloc
                http.authorizations.append(
                    httplib2.BasicAuthentication(
                        (_user, _password),
                        netloc,
                        dc_url,
                            {},
                        None,
                        None,
                        http
                    ))
                response, body = http.request(dc_url)
                doc = etree.fromstring(body)
                path = ".//{wcs}Axis/{wcs}AvailableKeys/{wcs}Key".format(wcs="{http://www.opengis.net/wcs/1.1.1}")
                atts = OrderedDict({})
                for n in doc.findall(path):
                    atts[n.attrib["name"]] = n.attrib["type"]
            except Exception:
                atts = {}
            return atts

    @property
    def display_type(self):
        return ({
            "dataStore" : "Vector Data",
            "coverageStore": "Raster Data",
            }).get(self.storeType, "Data")

    def delete_from_geoserver(self):
        cascading_delete(Layer.objects.gs_catalog, self.resource)

    def delete_from_geonetwork(self):
        gn = Layer.objects.gn_catalog
        gn.delete_layer(self)
        gn.logout()

    def save_to_geonetwork(self):
        gn = Layer.objects.gn_catalog
        record = gn.get_by_uuid(self.uuid)
        if record is None:
            md_link = gn.create_from_layer(self)
            self.metadata_links = [("text/xml", "TC211", md_link)]
        else:
            gn.update_layer(self)
        gn.logout()

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
            try:
                store = cat.get_store(self.store, ws)
                self._resource_cache = cat.get_resource(self.name, store)
            except Exception as e:
                logger.error("Store for %s does not exist: %s" % (self.name, str(e)))
                return None
        return self._resource_cache

    def _get_metadata_links(self):
        return self.resource.metadata_links

    def _set_metadata_links(self, md_links):
        try:
            self.resource.metadata_links = md_links
        except Exception, ex:
            logger.error("Exception occurred in _set_metadata_links for %s: %s", str(ex))

    metadata_links = property(_get_metadata_links, _set_metadata_links)

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
        ContactRole.objects.create(role=self.poc_role, layer=self, contact=poc)

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
        ContactRole.objects.create(role=self.metadata_author_role,
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
            gn = Layer.objects.gn_catalog
            self.resource.title = self.title
            self.resource.abstract = self.abstract
            self.resource.name= self.name
            self.resource.metadata_links = [('text/xml', 'TC211', gn.url_for_uuid(self.uuid))]
            self.resource.keywords = self.keyword_list()
            Layer.objects.gs_catalog.save(self._resource_cache)
            gn.logout()
        if self.poc and self.poc.user:
            self.publishing.attribution = str(self.poc.user)
            profile = Contact.objects.get(user=self.poc.user)
            self.publishing.attribution_link = settings.SITEURL[:-1] + profile.get_absolute_url()
            Layer.objects.gs_catalog.save(self.publishing)

    def  _populate_from_gs(self):
        gs_store = Layer.objects.gs_catalog.get_store(self.store)
        gs_resource = Layer.objects.gs_catalog.get_resource(self.name, gs_store)
        if gs_resource is None:
            return
        self.srs = gs_resource.projection
        self.llbbox = str([ max(-180,float(gs_resource.latlon_bbox[0])),max(-90,float(gs_resource.latlon_bbox[2])),min(180,float(gs_resource.latlon_bbox[1])),min(90,float(gs_resource.latlon_bbox[3]))])

        if self.srs == 'EPSG:4326':
            self.bbox = self.llbbox
        else:
            self.bbox = str([ float(gs_resource.native_bbox[0]),float(gs_resource.native_bbox[2]),float(gs_resource.native_bbox[1]),float(gs_resource.native_bbox[3])])

        if self.geographic_bounding_box is '' or self.geographic_bounding_box is None:
            self.set_bbox(gs_resource.native_bbox, srs=self.srs)
            ## Save using filter/update to avoid triggering post_save_layer
        Layer.objects.filter(id=self.id).update(srs = self.srs, llbbox = self.llbbox, bbox=self.bbox, geographic_bounding_box = self.geographic_bounding_box)

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
        kw_list = reduce(
            lambda x, y: x + y["keywords"],
            meta.identification.keywords,
            [])
        kw_list = [l for l in kw_list if l is not None]
        self.keywords.add(*kw_list)
        if hasattr(meta.distribution, 'online'):
            onlineresources = [r for r in meta.distribution.online if r.protocol == "WWW:LINK-1.0-http--link"]
            if len(onlineresources) == 1:
                res = onlineresources[0]
                self.distribution_url = res.url
                self.distribution_description = res.description

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

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
        return "/data/%s" % (self.typename)

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
        self.set_gen_level(CUSTOM_GROUP_USERS, self.LEVEL_READ)

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)

    def layer_config(self, user):
        """
        Generate a dict that can be serialized to a GXP layer configuration
        suitable for loading this layer.

        The "source" property will be left unset; the layer is not aware of the
        name assigned to its source plugin.  See
        :method:`geonode.maps.models.Map.viewer_json` for an example of
        generating a full map configuration.
        """
        cfg = dict()
        cfg['name'] = self.typename
        cfg['title'] =self.title
        cfg['transparent'] = True
        if self.topic_category:
            cfg['group'] = self.topic_category.title
        else:
            cfg['group'] = 'General'
        cfg['url'] = settings.GEOSERVER_BASE_URL + "wms"
        cfg['srs'] = self.srs
        cfg['bbox'] = json.loads(self.bbox)
        cfg['llbbox'] = json.loads(self.llbbox)
        cfg['queryable'] = (self.storeType == 'dataStore')
        cfg['attributes'] = self.layer_attributes()
        cfg['disabled'] =  user is not None and not user.has_perm('maps.view_layer', obj=self)
        cfg['visibility'] = True
        cfg['abstract'] = self.abstract
        cfg['styles'] = ''
        return cfg

    def queue_gazetteer_update(self):
        from geonode.queue.models import GazetteerUpdateJob
        if GazetteerUpdateJob.objects.filter(layer=self.id).exists() == 0:
            newJob = GazetteerUpdateJob(layer=self)
            newJob.save()

    def update_gazetteer(self):
        from geonode.gazetteer.utils import add_to_gazetteer, delete_from_gazetteer
        if not self.in_gazetteer:
            delete_from_gazetteer(self.name)
        else:
            includedAttributes = []
            gazetteerAttributes = self.attribute_set.filter(in_gazetteer=True)
            for attribute in gazetteerAttributes:
                includedAttributes.append(attribute.attribute)

            startAttribute = self.attribute_set.filter(is_gaz_start_date=True)[0].attribute if self.attribute_set.filter(is_gaz_start_date=True).exists() > 0 else None
            endAttribute = self.attribute_set.filter(is_gaz_end_date=True)[0].attribute if self.attribute_set.filter(is_gaz_end_date=True).exists() > 0 else None

            add_to_gazetteer(self.name,
                             includedAttributes,
                             start_attribute=startAttribute,
                             end_attribute=endAttribute,
                             project=self.gazetteer_project,
                             user=self.owner.username)

    def queue_bounds_update(self):
        from geonode.queue.models import LayerBoundsUpdateJob
        if LayerBoundsUpdateJob.objects.filter(layer=self.id).exists() == 0:
            newJob = LayerBoundsUpdateJob(layer=self)
            newJob.save()

    def update_bounds(self):
        #Get extent for layer from PostGIS
        bboxes = get_postgis_bbox(self.name, self.store)
        if len(bboxes) != 1 and len(bboxes[0]) != 2:
            return
        if bboxes[0][0] is None or bboxes[0][1] is None:
            return

        bbox = re.findall(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", bboxes[0][0])
        llbbox = re.findall(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", bboxes[0][1])

        #Assign new bbox to Layer
        self.bbox = str([float(l) for l in bbox])
        self.llbbox = str([float(l) for l in llbbox])
        self.set_bbox(bbox, srs=self.srs)

        #Update Geoserver bounding boxes
        resource_bbox = list(self.resource.native_bbox)
        resource_llbbox = list(self.resource.latlon_bbox)

        (resource_bbox[0],resource_bbox[1],resource_bbox[2],resource_bbox[3]) = str(bbox[0]), str(bbox[2]), str(bbox[1]), str(bbox[3])
        (resource_llbbox[0],resource_llbbox[1],resource_llbbox[2],resource_llbbox[3]) = str(llbbox[0]), str(llbbox[2]), str(llbbox[1]), str(llbbox[3])

        self.resource.native_bbox = tuple(resource_bbox)
        self.resource.latlon_bbox = tuple(resource_llbbox)
        Layer.objects.gs_catalog.save(self._resource_cache)


        # Use update to avoid unnecessary post_save signal
        Layer.objects.filter(id=self.id).update(bbox=self.bbox,llbbox=self.llbbox,geographic_bounding_box=self.geographic_bounding_box )

        #Update geonetwork record with latest extent
        logger.info("Save new bounds to geonetwork")
        self.save_to_geonetwork()


class LayerAttributeManager(models.Manager):
    """Helper class to access filtered attributes
    """
    def visible(self):
        return self.get_query_set().filter(visible=True).order_by('display_order')

class LayerAttribute(models.Model):
    objects = LayerAttributeManager()

    layer = models.ForeignKey(Layer, blank=False, null=False, unique=False, related_name='attribute_set')
    #layer = models.ForeignKey(ResourceBase, blank=False, null=False, unique=False, related_name='attribute_set')

    attribute = models.CharField(_('Attribute Name'), max_length=255, blank=False, null=True, unique=False)
    attribute_label = models.CharField(_('Attribute Label'), max_length=255, blank=False, null=True, unique=False)
    attribute_type = models.CharField(_('Attribute Type'), max_length=50, blank=False, null=False, default='xsd:string', unique=False)
    searchable = models.BooleanField(_('Searchable?'), default=False)
    visible = models.BooleanField(_('Visible?'), default=True)
    display_order = models.IntegerField(_('Display Order'), default=1)
    in_gazetteer = models.BooleanField(_('In Gazetteer?'), default=False)
    is_gaz_start_date = models.BooleanField(_('Gazetteer Start Date'), default=False)
    is_gaz_end_date = models.BooleanField(_('Gazetteer End Date'), default=False)
    date_format = models.CharField(_('Date Format'), max_length=255, blank=True, null=True)

    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the object was created.
    """

    last_modified = models.DateTimeField(auto_now=True)
    """
    The last time the object was modified.
    """

    def __str__(self):
        return "%s" % self.attribute

    def __unicode__(self):
        return self.attribute


class Map(models.Model, PermissionLevelMixin):
    """
    A Map aggregates several layers together and annotates them with a viewport
    configuration.
    """

    title = models.TextField(_('Title'))
    # A display name suitable for search results and page headers

    abstract = models.TextField(_('Abstract'), blank=True)
    # A longer description of the themes in the map.

    # viewer configuration
    zoom = models.IntegerField(_('zoom'))
    # The zoom level to use when initially loading this map.  Zoom levels start
    # at 0 (most zoomed out) and each increment doubles the resolution.

    projection = models.CharField(_('projection'),max_length=32)
    # The projection used for this map.  This is stored as a string with the
    # projection's SRID.

    center_x = models.FloatField(_('center X'))
    # The x coordinate to center on when loading this map.  Its interpretation
    # depends on the projection.

    center_y = models.FloatField(_('center Y'))
    # The y coordinate to center on when loading this map.  Its interpretation
    # depends on the projection.

    owner = models.ForeignKey(User, verbose_name=_('owner'), blank=True, null=True)
    # The user that created/owns this map.

    created_dttm = models.DateTimeField(_("Date Created"), auto_now_add=True)
    """
    The date/time the map was created.
    """

    keywords = TaggableManager(_('keywords'), help_text=_("A space or comma-separated list of keywords"), blank=True)

    last_modified = models.DateTimeField(_("Date Last Modified"),auto_now=True)
    """
    The last time the map was modified.
    """

    urlsuffix = models.CharField(_('Site URL'), max_length=255, blank=True)
    """
    Alphanumeric alternative to referencing maps by id, appended to end of URL instead of id, ie http://domain/maps/someview
    """

    officialurl = models.CharField(_('Official Harvard Site URL'), max_length=255, blank=True)
    """
    Full URL for official/sponsored map view, ie http://domain/someview
    """

    content = models.TextField(_('Site Content'), blank=True, null=True, default=DEFAULT_CONTENT)
    """
    HTML content to be displayed in modal window on 1st visit
    """

    use_custom_template = models.BooleanField(_('Use a custom template'),default=False)
    """
    Whether to show default banner/styles or custom ones.
    """

    group_params = models.TextField(_('Layer Category Parameters'), blank=True)
    """
    Layer categories (names, expanded)
    """

    template_page = models.CharField('Map template page',  max_length=255, blank=True)
    """
    The map view template page to use, if different from default
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
    def maplayers(self):
        layers = cache.get('maplayerset_' + str(self.id))
        if layers is None:
            logger.debug('maplayerset cache was None')
            layers = MapLayer.objects.filter(map=self.id).order_by('stack_order')
            cache.add('maplayerset_' + str(self.id), layers)
        return  [layer for layer in layers]


    @property
    def snapshots(self):
        snapshots = MapSnapshot.objects.exclude(user=None).filter(map=self.id)
        return [snapshot for snapshot in snapshots]

    @property
    def layers(self):
        layers = MapLayer.objects.filter(map=self.id)
        return  [layer for layer in layers]

    @property
    def local_layers(self):
        return True

    def json(self, layer_filter):
        map_layers = MapLayer.objects.filter(map=self.id)
        layers = []
        for map_layer in map_layers:
            if map_layer.local():
                layer =  Layer.objects.get(typename=map_layer.name)
                layers.append(layer)
            else:
                pass

        if layer_filter:
            layers = [l for l in layers if layer_filter(l)]

        readme = (
                     "Title: %s\n" +
                     "Author: %s\n"
                     "Abstract: %s\n"
                     ) % (self.title, "The GeoNode Team", self.abstract)

        def layer_json(lyr):
            return {
                "name": lyr.typename,
                "service": lyr.service_type,
                "serviceURL": "",
                "metadataURL": ""
            }

        map_config = {
            "map" : { "readme": readme },
            "layers" : [layer_json(lyr) for lyr in layers]
        }

        return json.dumps(map_config)

    def viewer_json(self, user=None, *added_layers):
        """
        Convert this map to a nested dictionary structure matching the JSON
        configuration for GXP Viewers.

        The ``added_layers`` parameter list allows a list of extra MapLayer
        instances to append to the Map's layer list when generating the
        configuration. These are not persisted; if you want to add layers you
        should use ``.layer_set.create()``.
        """
        layers = list(self.maplayers) + list(added_layers) #implicitly sorted by stack_order

        sejumps = self.jump_set.all()
        server_lookup = {}
        sources = {'local': settings.DEFAULT_LAYER_SOURCE }

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


        def uniqifydict(seq, item):
            """
            get a list of unique dictionary elements based on a certain  item (ie 'group').
            """
            results = []
            items = []
            for x in seq:
                if x[item] not in items:
                    items.append(x[item])
                    results.append(x)
            return results

        configs = [l.source_config() for l in layers]
        configs.append({"ptype":"gxp_gnsource", "url": settings.GEOSERVER_BASE_URL + "wms", "restUrl":"/gs/rest"})

        i = 0
        for source in uniqify(configs):
            while str(i) in sources: i = i + 1
            sources[str(i)] = source
            server_lookup[json.dumps(source)] = str(i)

        def source_lookup(source):
            for k, v in sources.iteritems():
                if v == source: return k
            return None

        def layer_config(l, user):
            logger.debug("_________CALLING viewer_json.layer_config for %s", l)
            cfg = l.layer_config(user)
            src_cfg = l.source_config()
            source = source_lookup(src_cfg)
            if source: cfg["source"] = source
            if src_cfg.get("ptype", "gxp_wmscsource") == "gxp_wmscsource"  or src_cfg.get("ptype", "gxp_gnsource") == "gxp_gnsource" : cfg["buffer"] = 0
            return cfg

        config = {
            'id': self.id,
            'about': {
                'title':   self.title,
                'abstract': self.abstract,
                'urlsuffix': self.urlsuffix,
                'introtext' : self.content,
                'officialurl' : self.officialurl
            },
            'defaultSourceType': "gxp_gnsource",
            'sources': sources,
            'map': {
                'layers': [layer_config(l, user) for l in layers],
                'center': [self.center_x, self.center_y],
                'projection': self.projection,
                'zoom': self.zoom,

                },
            'social_explorer': [se.json() for se in sejumps]
        }


        if self.group_params:
            #config["treeconfig"] = json.loads(self.group_params)
            config["map"]["groups"] = uniqifydict(json.loads(self.group_params), 'group')

        '''
        # Mark the last added layer as selected - important for data page
        '''
        config["map"]["layers"][len(layers)-1]["selected"] = True

        config["map"].update(_get_viewer_projection_info(self.projection))


        return config

    def update_from_viewer(self, conf):
        from django.utils.html import escape
        """
        Update this Map's details by parsing a JSON object as produced by
        a GXP Viewer.

        This method automatically persists to the database!
        """
        if isinstance(conf, basestring):
            conf = json.loads(conf)

        self.title = despam(conf['about']['title'])
        self.abstract = despam(conf['about']['abstract'])
        self.urlsuffix = conf['about']['urlsuffix']

        x = XssCleaner()
        self.content = despam(x.strip(conf['about']['introtext']))

        #self.content = re.sub(r'<script.*(<\/script>|\/>)|javascript:|\$\(|jQuery|Ext\.', r'', conf['about']['introtext']) #Remove any scripts
        #self.keywords = despam(conf['about']['keywords'])
        self.zoom = conf['map']['zoom']

        self.center_x = conf['map']['center'][0]
        self.center_y = conf['map']['center'][1]

        self.projection = conf['map']['projection']

        self.featured = conf['about'].get('featured', False)

        logger.debug("Try to save treeconfig")
        if 'groups' in conf['map']:
            self.group_params = json.dumps(conf['map']['groups'])
        logger.debug("Saved treeconfig")

        def source_for(layer):
            return conf["sources"][layer["source"]]

        layers = [l for l in conf["map"]["layers"]]

        for layer in self.layer_set.all():
            layer.delete()

        self.keywords.add(*conf['map'].get('keywords', []))

        for ordering, layer in enumerate(layers):
            self.layer_set.add(
                self.layer_set.from_viewer_config(
                    self, layer, source_for(layer), ordering
                ))
        self.save()
        cache.delete('maplayerset_' + str(self.id))

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

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
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ)
        self.set_gen_level(CUSTOM_GROUP_USERS, self.LEVEL_READ)

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)


class MapSnapshot(models.Model):
    map = models.ForeignKey(Map, related_name="snapshot_set")
    """
    The ID of the map this snapshot was generated from.
    """

    config = models.TextField(_('JSON Configuration'))
    """
    Map configuration in JSON format
    """

    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the snapshot was created.
    """

    user = models.ForeignKey(User, blank=True, null=True)
    """
    The user who created the snapshot.
    """

    def json(self):
        return {
            "map": self.map.id,
            "created": self.created_dttm.isoformat(),
            "user": self.user.username if self.user else None,
            "url": num_encode(self.id)
        }




class SocialExplorerLocation(models.Model):
    map = models.ForeignKey(Map, related_name="jump_set")
    url = models.URLField(_("Jump URL"), blank=False, null=False, default='http://www.socialexplorer.com/pub/maps/map3.aspx?g=0&mapi=SE0012&themei=B23A1CEE3D8D405BA2B079DDF5DE9402')
    title = models.TextField(_("Jump Site"), blank=False, null=False)

    def json(self):
        logger.debug("JSON url: %s", self.url)
        return {
            "url": self.url,
            "title" :  self.title
        }

class MapLayerManager(models.Manager):
    def from_viewer_config(self, map_model, layer, source, ordering):
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
                  "fixed", "group", "visibility", "source"]:
            if k in layer_cfg: del layer_cfg[k]

        source_cfg = dict(source)
        for k in ["url", "projection"]:
            if k in source_cfg: del source_cfg[k]

        return self.model(
            map = map_model,
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
            layer_params = json.dumps(layer_cfg),
            source_params = json.dumps(source_cfg)
        )

class MapLayer(models.Model):
    """
    The MapLayer model represents a layer included in a map.  This doesn't just
    identify the dataset, but also extra options such as which style to load
    and the file format to use for image tiles.
    """

    objects = MapLayerManager()
    # see :class:`geonode.maps.models.MapLayerManager`

    map = models.ForeignKey(Map, related_name="layer_set")
    # The map containing this layer

    stack_order = models.IntegerField(_('stack order'))
    # The z-index of this layer in the map; layers with a higher stack_order will
    # be drawn on top of others.

    format = models.CharField(_('format'), blank=True, null=True, max_length=200)
    # The mimetype of the image format to use for tiles (image/png, image/jpeg,
    # image/gif...)

    name = models.CharField(_('name'), blank=True, null=True, max_length=200)
    # The name of the layer to load.

    # The interpretation of this name depends on the source of the layer (Google
    # has a fixed set of names, WMS services publish a list of available layers
    # in their capabilities documents, etc.)

    opacity = models.FloatField(_('opacity'), default=1.0)
    # The opacity with which to render this layer, on a scale from 0 to 1.

    styles = models.CharField(_('styles'), blank=True, null=True,max_length=200)
    # The name of the style to use for this layer (only useful for WMS layers.)

    transparent = models.BooleanField(_('transparent'))
    # A boolean value, true if we should request tiles with a transparent background.

    fixed = models.BooleanField(_('fixed'), default=False)
    # A boolean value, true if we should prevent the user from dragging and
    # dropping this layer in the layer chooser.

    group = models.CharField(_('group'), null=True,max_length=200)
    # A group label to apply to this layer.  This affects the hierarchy displayed
    # in the map viewer's layer tree.

    visibility = models.BooleanField(_('visibility'), default=True)
    # A boolean value, true if this layer should be visible when the map loads.

    ows_url = models.URLField(_('ows URL'), blank=True, null=True)
    # The URL of the OWS service providing this layer, if any exists.

    layer_params = models.TextField(_('layer params'))
    # A JSON-encoded dictionary of arbitrary parameters for the layer itself when
    # passed to the GXP viewer.

    # If this dictionary conflicts with options that are stored in other fields
    # (such as format, styles, etc.) then the fields override.

    source_params = models.TextField(_('source params'))
    # A JSON-encoded dictionary of arbitrary parameters for the GXP layer source
    # configuration for this layer.

    # If this dictionary conflicts with options that are stored in other fields
    # (such as ows_url) then the fields override.


    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the object was created.
    """

    last_modified = models.DateTimeField(auto_now=True)
    """
    The last time the object was modified.
    """

    def local(self):
        """
        Tests whether this layer is served by the GeoServer instance that is
        paired with the GeoNode site.  Currently this is based on heuristics,
        but we try to err on the side of false negatives.
        """
        isLocal = False
        if self.ows_url:
            ows_url = urlparse(self.ows_url)
            settings_url = urlparse(settings.GEOSERVER_BASE_URL + "wms")
            if settings_url.netloc == ows_url.netloc and settings_url.path == ows_url.path:
                isLocal = cache.get('islocal_' + self.name)
                if isLocal is None:
                    isLocal = Layer.objects.filter(typename=self.name).count() != 0
                    cache.add('islocal_' + self.name, isLocal)
        return isLocal


    def source_config(self):
        """
        Generate a dict that can be serialized to a GXP layer source
        configuration suitable for loading this layer.
        """
        try:
            cfg = json.loads(self.source_params)
        except Exception:
            cfg = dict(ptype = "gxp_gnsource", restUrl="/gs/rest")

        if self.ows_url:
            cfg["url"] = ows_sub.sub('',self.ows_url)
            if "ptype" not in cfg:
                cfg["ptype"] = "gxp_wmscsource"

        if "ptype" in cfg and cfg["ptype"] == "gxp_gnsource":
            cfg["restUrl"] = "/gs/rest"
        return cfg

    def layer_config(self, user):
        """
        Generate a dict that can be serialized to a GXP layer configuration
        suitable for loading this layer.

        The "source" property will be left unset; the layer is not aware of the
        name assigned to its source plugin.  See
        :method:`geonode.maps.models.Map.viewer_json` for an example of
        generating a full map configuration.
        """
        #       Caching of  maplayer config, per user (due to permissions)
        if self.id is not None:
            cfg = cache.get("maplayer_config_" + str(self.id) + "_" + str(0 if user is None else user.id))
            if cfg is not None:
                logger.debug("Cached cfg: %s", str(cfg))
                return cfg

        try:
            cfg = json.loads(self.layer_params)
        except Exception:
            cfg = dict()

        if self.format: cfg['format'] = self.format
        if self.name: cfg["name"] = self.name
        if self.opacity: cfg['opacity'] = self.opacity
        if self.styles: cfg['styles'] = self.styles
        if self.transparent: cfg['transparent'] = True

        cfg["fixed"] = self.fixed
        if 'url' not in cfg:
            cfg['url'] = self.ows_url
        if cfg['url']:
            cfg['url'] = ows_sub.sub('', cfg['url'])
        if self.group: cfg["group"] = self.group
        cfg["visibility"] = self.visibility

        if self.name is not None and self.source_params.find( "gxp_gnsource") > -1:
            #Get parameters from GeoNode instead of WMS GetCapabilities
            try:
                gnLayer = Layer.objects.get(typename=self.name)
                if gnLayer.srs: cfg['srs'] = gnLayer.srs
                if gnLayer.bbox: cfg['bbox'] = json.loads(gnLayer.bbox)
                if gnLayer.llbbox: cfg['llbbox'] = json.loads(gnLayer.llbbox)
                cfg['attributes'] = (gnLayer.layer_attributes())
                attribute_cfg = gnLayer.attribute_config()
                if "getFeatureInfo" in attribute_cfg:
                    cfg["getFeatureInfo"] = attribute_cfg["getFeatureInfo"]
                cfg['queryable'] = (gnLayer.storeType == 'dataStore'),
                cfg['disabled'] =  user is not None and not user.has_perm('maps.view_layer', obj=gnLayer)
                #cfg["displayOutsideMaxExtent"] = user is not None and  user.has_perm('maps.change_layer', obj=gnLayer)
                cfg['visibility'] = cfg['visibility'] and not cfg['disabled']
                cfg['abstract'] = gnLayer.abstract
                cfg['styles'] = self.styles
            except Exception, e:
                # Give it some default values so it will still show up on the map, but disable it in the layer tree
                cfg['srs'] = 'EPSG:900913'
                cfg['llbbox'] = [-180,-90,180,90]
                cfg['attributes'] = []
                cfg['queryable'] =False,
                cfg['disabled'] = False
                cfg['visibility'] = cfg['visibility'] and not cfg['disabled']
                cfg['abstract'] = ''
                cfg['styles'] =''
                logger.info("Could not retrieve Layer with typename of %s : %s", self.name, str(e))
        elif self.source_params.find( "gxp_hglsource") > -1:
            # call HGL ServiceStarter asynchronously to load the layer into HGL geoserver
            from geonode.queue.tasks import loadHGL
            loadHGL.delay(self.name)


        #Create cache of maplayer config that will last for 60 seconds (in case permissions or maplayer properties are changed)
        if self.id is not None:
            cache.set("maplayer_config_" + str(self.id) + "_" + str(0 if user is None else user.id), cfg, 60)
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


def pre_save_maplayer(instance, sender, **kwargs):

    if instance.local():
        print 'Fixing layer_params url for layer %s' % instance.name
        instance.layer_params = instance.layer_params.replace('https://', 'http://')

signals.pre_save.connect(pre_save_maplayer, sender=MapLayer)


class Role(models.Model):
    """
    Roles are a generic way to create groups of permissions.
    """
    value = models.CharField('Role', choices= [(x, x) for x in ROLE_VALUES], max_length=255, unique=True)
    permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'), blank=True)

    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the object was created.
    """

    last_modified = models.DateTimeField(auto_now=True)
    """
    The last time the object was modified.
    """

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
            contacts = self.layer.contacts.filter(contactrole__role=self.role)
            if contacts.count() == 1:
                # only allow this if we are updating the same contact
                if self.contact != contacts.get():
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
    if settings.USE_GAZETTEER and instance.in_gazetteer:
        instance.in_gazetteer = False
        instance.update_gazetteer()

def post_save_layer(instance, sender, **kwargs):
    instance._autopopulate()
    #Don't save to geoserver if storeType isn't populated yet; do it later
    if (re.search("coverageStore|dataStore", instance.storeType)):
        logger.info("Call save_to_geoserver for %s", instance.name)
        instance.save_to_geoserver()
        if kwargs['created']:
            instance._populate_from_gs()

signals.pre_delete.connect(delete_layer, sender=Layer)
signals.post_save.connect(post_save_layer, sender=Layer)



#===================#
#    NEW WORLDMAP MODELS      #
#===================#

class MapStats(models.Model):
    map = models.ForeignKey(Map, unique=True)
    visits = models.IntegerField(_("Visits"), default= 0)
    uniques = models.IntegerField(_("Unique Visitors"), default = 0)
    last_modified = models.DateTimeField(auto_now=True,null=True)

    class Meta:
        verbose_name_plural = 'Map stats'

class LayerStats(models.Model):
    layer = models.ForeignKey(Layer, unique=True)
    visits = models.IntegerField(_("Visits"), default = 0)
    uniques = models.IntegerField(_("Unique Visitors"), default = 0)
    downloads = models.IntegerField(_("Downloads"), default = 0)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = 'Layer stats'
