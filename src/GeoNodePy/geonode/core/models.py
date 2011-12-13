# -*- coding: UTF-8 -*-
from django.contrib.auth import authenticate, get_backends as get_auth_backends
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext_lazy as _


class ObjectRoleManager(models.Manager):
    def get_by_natural_key(self, codename, app_label, model):
        return self.get(
            codename=codename,
            content_type=ContentType.objects.get_by_natural_key(app_label, model)
        )

class ObjectRole(models.Model):
    """
    A bundle of object permissions representing 
    the rights associated with having a 
    particular role with respect to an object.
    """
    objects = ObjectRoleManager()

    title = models.CharField(_('title'), max_length=255) 
    permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'))
    codename = models.CharField(_('codename'), max_length=100, unique=True)
    content_type = models.ForeignKey(ContentType)
    list_order = models.IntegerField(help_text=_("Determines the order that roles are presented in the user interface."))

    def __unicode__(self):
        return "%s | %s" % (self.content_type, self.title)

    class Meta:
        unique_together = (('content_type', 'codename'),)

    def natural_key(self):
        return (self.codename,) + self.content_type.natural_key()


class UserObjectRoleMapping(models.Model):
    """
    represents assignment of a role to a particular user 
    in the context of a specific object.
    """

    user = models.ForeignKey(User, related_name="role_mappings")
    
    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_ct', 'object_id')

    role = models.ForeignKey(ObjectRole, related_name="user_mappings")

    def __unicode__(self):
        return u"%s | %s -> %s" % (
            unicode(self.object),
            unicode(self.user), 
            unicode(self.role))

    class Meta:
        unique_together = (('user', 'object_ct', 'object_id', 'role'), ) 

# implicitly defined 'generic' groups of users 
ANONYMOUS_USERS = 'anonymous'
AUTHENTICATED_USERS = 'authenticated'
GENERIC_GROUP_NAMES = {
    ANONYMOUS_USERS: _('Anonymous Users'),
    AUTHENTICATED_USERS: _('Registered Users')
}

class GenericObjectRoleMapping(models.Model):
    """
    represents assignment of a role to an arbitrary implicitly 
    defined group of users (groups without explicit database representation) 
    in the context of a specific object. eg 'all authenticated users' 
    'anonymous users', 'users <as defined by some other service>'
    """
    
    subject = models.CharField(max_length=100, choices=sorted(GENERIC_GROUP_NAMES.items()))

    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_ct', 'object_id')

    role = models.ForeignKey(ObjectRole, related_name="generic_mappings")

    def __unicode__(self):
        return u"%s | %s -> %s" % (
            unicode(self.object),
            unicode(GENERIC_GROUP_NAMES[self.subject]), 
            unicode(self.role))

    class Meta:
        unique_together = (('subject', 'object_ct', 'object_id', 'role'), )

class PermissionLevelError(Exception):
    pass

class PermissionLevelMixin(object):
    """
    Mixin for adding "Permission Level" methods 
    to a model class -- eg role systems where a 
    user has exactly one assigned role with respect to 
    an object representing an "access level"
    """

    LEVEL_NONE = "_none"

    @property
    def permission_levels(self):
        """
        A list of available levels in order.
        """
        levels = [self.LEVEL_NONE]
        content_type = ContentType.objects.get_for_model(self)
        for role in ObjectRole.objects.filter(content_type=content_type).order_by('list_order'):
            levels.append(role.codename)
        return levels
        
    def get_user_level(self, user):
        """
        get the permission level (if any) specifically assigned to the given user.
        Returns LEVEL_NONE to indicate no specific level has been assigned.
        """
        try:
            my_ct = ContentType.objects.get_for_model(self)
            mapping = UserObjectRoleMapping.objects.get(user=user, object_id=self.id, object_ct=my_ct)
            return mapping.role.codename
        except:
            return self.LEVEL_NONE

    def set_user_level(self, user, level):
        """
        set the user's permission level to the level specified. if 
        level is LEVEL_NONE, any existing level assignment is removed.
        """
        
        my_ct = ContentType.objects.get_for_model(self)
        if level == self.LEVEL_NONE:
            UserObjectRoleMapping.objects.filter(user=user, object_id=self.id, object_ct=my_ct).delete()
        else:
            # lookup new role...
            try:
                role = ObjectRole.objects.get(codename=level, content_type=my_ct)
            except ObjectRole.NotFound: 
                raise PermissionLevelError("Invalid Permission Level (%s)" % level)
            # remove any existing mapping              
            UserObjectRoleMapping.objects.filter(user=user, object_id=self.id, object_ct=my_ct).delete()
            # grant new level
            UserObjectRoleMapping.objects.create(user=user, object=self, role=role)

    def get_gen_level(self, gen_role):
        """
        get the permission level (if any) specifically assigned to the given generic
        group of users.  Returns LEVEL_NONE to indicate no specific level has been assigned.
        """

        try:
            my_ct = ContentType.objects.get_for_model(self)
            mapping = GenericObjectRoleMapping.objects.get(subject=gen_role, object_id=self.id, object_ct=my_ct)
            return mapping.role.codename
        except:
            return self.LEVEL_NONE

    def set_gen_level(self, gen_role, level):
        """
        grant the permission level specified to the generic group of 
        users specified.  if level is LEVEL_NONE, any existing assignment is 
        removed.
        """
        
        my_ct = ContentType.objects.get_for_model(self)
        if level == self.LEVEL_NONE:
            GenericObjectRoleMapping.objects.filter(subject=gen_role, object_id=self.id, object_ct=my_ct).delete()
        else:
            try:
                role = ObjectRole.objects.get(codename=level, content_type=my_ct)
            except ObjectRole.DoesNotExist: 
                raise PermissionLevelError("Invalid Permission Level (%s)" % level)
            # remove any existing mapping              
            GenericObjectRoleMapping.objects.filter(subject=gen_role, object_id=self.id, object_ct=my_ct).delete()
            # grant new level
            GenericObjectRoleMapping.objects.create(subject=gen_role, object=self, role=role)

    def get_user_levels(self):
        ct = ContentType.objects.get_for_model(self)
        return UserObjectRoleMapping.objects.filter(object_id = self.id, object_ct = ct)

    def get_generic_levels(self):
        ct = ContentType.objects.get_for_model(self)
        return GenericObjectRoleMapping.objects.filter(object_id = self.id, object_ct = ct)

    def get_all_level_info(self):
        """
        returns a mapping indicating the permission levels
        of users, anonymous users any authenticated users that
        have specific permissions assigned to them.

        if a key is not present it indicates that no level
        has been assigned. 
        
        the mapping looks like: 
        {
            'anonymous': 'readonly', 
            'authenticated': 'readwrite',
            'users': {
                <username>: 'admin'
                ...
            }
        }
        """
        my_ct = ContentType.objects.get_for_model(self)

        # get all user-specific permissions
        user_levels = {}
        for rm in UserObjectRoleMapping.objects.filter(object_id=self.id, object_ct=my_ct).all():
            user_levels[rm.user.username] = rm.role.codename

        levels = {}
        for rm in GenericObjectRoleMapping.objects.filter(object_id=self.id, object_ct=my_ct).all():
            levels[rm.subject] = rm.role.codename
        levels['users'] = user_levels

        return levels

# Logic to login a user automatically when it has successfully
# activated an account:
from registration.signals import user_activated
from django.contrib.auth import login

def autologin(sender, **kwargs):
    user = kwargs['user']
    request = kwargs['request']
    # Manually setting the default user backed to avoid the
    # 'User' object has no attribute 'backend' error
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    # This login function does not need password.
    login(request, user)

user_activated.connect(autologin)

# Common internationalization choices for shared models.
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
