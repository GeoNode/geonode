import random
import string
import ldap
import ldap.modlist
import geocoder
import geonode.settings as settings
from osgeo import ogr

from pprint import pprint
from unidecode import unidecode
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.utils import simplejson as json
from django.utils import dateformat
from django.utils.translation import ugettext_lazy as _

from geonode.people.models import Profile
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.cephgeo.models import UserJurisdiction, UserTiles, TileDataClass
from geonode.cephgeo.models import CephDataObject
import geocoder

UNALLOWED_USERNAME_CHARACTERS='"[]:;|=+*?<>/\,.'
ESCAPED_CHARACTERS="/\,"

def create_login_credentials(data_request):

    first_name = unidecode(data_request.first_name)
    first_name_f = ""
    for i in first_name.lower().split():
        first_name_f += i[0]

    middle_name_f= "".join(unidecode(data_request.middle_name).split())[0]
    last_name_f = "".join(unidecode(data_request.last_name).split())

    base_username = (first_name_f + middle_name_f + last_name_f).lower()

    for x in base_username:
        if x in UNALLOWED_USERNAME_CHARACTERS:
            base_username = base_username.replace(x,'')

    unique = False
    counter = 0
    final_username = base_username
    username_list = get_unames_starting_with(base_username)
    while not unique:
        if counter > 0:
            final_username = final_username + str(counter)

        for x,y in username_list:
            if x is None:
                unique = True
            else:
                if final_username == y["sAMAccountName"][0]:
                    counter += 1
                    unique=False
                    break
                else:
                    unique=True

    return final_username

def string_randomizer(length):
    word = ""
    for i in range(length):
        word += random.choice(string.lowercase+string.uppercase+string.digits+UNALLOWED_USERNAME_CHARACTERS+ESCAPED_CHARACTERS)
    return word

def get_unames_starting_with(name):
    result = []
    try:
        con =ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        con.set_option(ldap.OPT_REFERRALS, 0)
        con.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
        result = con.search_s(settings.AUTH_LDAP_BASE_DN, ldap.SCOPE_SUBTREE, "(sAMAccountName="+name+"*)", ["sAMAccountName"])
        con.unbind_s()
    except Exception as e:
        print '%s (%s)' % (e.message, type(e))
        return e
    return result

def create_ad_account(profilerequest, username):
    objectClass =  ["organizationalPerson", "person", "top", "user"]
    sAMAccountName = str(username)
    password = unicode("\""+string_randomizer(16)+"\"", "iso-8859-1").encode("utf-16-le")
    sn= unidecode(profilerequest.last_name)
    givenName = unidecode(profilerequest.first_name)
    initials=unidecode(profilerequest.middle_name[0])
    cn = unidecode(givenName+" "+profilerequest.middle_name+" "+sn)
    displayName=unidecode(givenName+" "+initials+". "+sn)
    telephoneNumber = str(profilerequest.contact_number)
    mail=str(profilerequest.email)
    userPrincipalName=str(username+"@ad.dream.upd.edu.ph")
    userAccountControl = "512"
    o=unidecode(profilerequest.organization)
    company = unidecode(profilerequest.org_type)   # Added setting of org_type to company AD field

    for c in cn:
        if c in ESCAPED_CHARACTERS:
            cn = cn.replace(c, '')


    dn="CN="+cn+","+settings.LIPAD_LDAP_BASE_DN
    modList = {
        "objectClass": objectClass,
        "sAMAccountName": [sAMAccountName],
        "sn": [sn],
        "unicodePwd": [password],
        "givenName": [givenName],
        "cn":[cn],
        "displayName": [displayName],
        "mail": [mail],
        "userPrincipalName": [userPrincipalName],
        "userAccountControl": [userAccountControl],
        "telephoneNumber": [telephoneNumber],
        "o": [o],
        "company": [company],
        "initials": [initials]
    }

    try:
        con = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        con.set_option(ldap.OPT_REFERRALS, 0)
        con.simple_bind_s(settings.LIPAD_LDAP_BIND_DN, settings.LIPAD_LDAP_BIND_PW)
        result = con.add_s(dn,ldap.modlist.addModlist(modList))
        con.unbind_s()
        pprint(result)
        return dn
    except Exception as e:
        import traceback
        print traceback.format_exc()
        raise e

def add_to_ad_group(group_dn=settings.LIPAD_LDAP_GROUP_DN, user_dn=""):
    try:
        add_user_mod = [(ldap.MOD_ADD, "member", user_dn)]
        con = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        con.set_option(ldap.OPT_REFERRALS, 0)
        con.simple_bind_s(settings.LIPAD_LDAP_BIND_DN, settings.LIPAD_LDAP_BIND_PW)
        group_result = con.modify_s(group_dn, add_user_mod)
        con.unbind_s()
        pprint(group_result)
        return group_result
    except Exception as e:
        import traceback
        print traceback.format_exc()
        return e

def get_place_name(longitude,latitude):
    g = geocoder.google([latitude,longitude], method='reverse')
    # pprint(g.geojson)
    return {
        'street': g.street,
        'city': g.city,
        'county': g.county,
        'state': g.state,
        'country': g.country,
        'address': g.address
    }

def get_juris_data_size(juris_shp_name):
    juris_shp = get_shp_ogr(juris_shp_name)

    _TILE_SIZE = 1000
    total_data_size = 0
    min_x =  int(math.floor(juris_shp.bounds[0] / float(_TILE_SIZE)) * _TILE_SIZE)
    max_x =  int(math.ceil(juris_shp.bounds[2] / float(_TILE_SIZE)) * _TILE_SIZE)
    min_y =  int(math.floor(juris_shp.bounds[1] / float(_TILE_SIZE)) * _TILE_SIZE)
    max_y =  int(math.ceil(juris_shp.bounds[3] / float(_TILE_SIZE)) * _TILE_SIZE)
    for tile_y in xrange(min_y+_TILE_SIZE, max_y+_TILE_SIZE, _TILE_SIZE):
        for tile_x in xrange(min_x, max_x, _TILE_SIZE):
            tile_ulp = (tile_x, tile_y)
            tile_dlp = (tile_x, tile_y - _TILE_SIZE)
            tile_drp = (tile_x + _TILE_SIZE, tile_y - _TILE_SIZE)
            tile_urp = (tile_x + _TILE_SIZE, tile_y)
            tile = Polygon([tile_ulp, tile_dlp, tile_drp, tile_urp])

            if not tile.intersection(juris_shp).is_empty:
                gridref = "E{0}N{1}".format(tile_x / _TILE_SIZE, tile_y / _TILE_SIZE,)
                # georef_query = CephDataObject.objects.filter(name__startswith=gridref)
                georef_query = CephDataObject.objects.filter(name__startswith=gridref)
                total_size = 0
                for georef_query_objects in georef_query:
                    total_size += georef_query_objects.size_in_bytes
                total_data_size += total_size
    return total_data_size

def get_area_coverage(geoms):
    area = 0

    for g in geoms:
        area += g.area

    return area/1000000


def get_shp_ogr(juris_shp_name):
    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(settings.DATABASE_HOST,settings.DATASTORE_DB,settings.DATABASE_USER,settings.DATABASE_PASSWORD)))
    data = source.ExecuteSQL("select the_geom from "+str(juris_shp_name))
    shplist = []
    if data:
        for i in range(data.GetFeatureCount()):
            feature = data.GetNextFeature()
            shplist.append(loads(feature.GetGeometryRef().ExportToWkb()))
        juris_shp = cascaded_union(shplist)
        return juris_shp
    else:
        return None

def data_class_choices():
    choices =[]
    for dc in TileDataClass.objects.all():
        choices.append((dc.short_name, _(dc.full_name)))

    return tuple(choices)
