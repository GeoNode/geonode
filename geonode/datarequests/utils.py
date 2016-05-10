import random
import string
import ldap
import ldap.modlist
import geonode.settings as settings

from pprint import pprint
from unidecode import unidecode
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404

from geonode.people.models import Profile
from geonode.documents.models import Document

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

def create_ad_account(datarequest, username):
    objectClass =  ["organizationalPerson", "person", "top", "user"]
    sAMAccountName = str(username)
    password = unicode("\""+string_randomizer(16)+"\"", "iso-8859-1").encode("utf-16-le")
    sn= unidecode(datarequest.last_name)
    givenName = unidecode(datarequest.first_name)
    initials=unidecode(datarequest.middle_name[0])
    cn = unidecode(givenName+" "+datarequest.middle_name+". "+sn)
    displayName=unidecode(givenName+" "+initials+". "+sn)
    telephoneNumber = str(datarequest.contact_number)
    mail=str(datarequest.email)
    userPrincipalName=str(username+"@ad.dream.upd.edu.ph")
    userAccountControl = "512"
    ou=str(datarequest.organization)
    
    for c in cn:
        if c in ESCAPED_CHARACTERS:
            cn = cn.replace(c, '')
            
    for c in ou:
        if c in ESCAPED_CHARACTERS:
            ou = ou.replace(c,'\\'+c)
            
    
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
        "ou": [ou]
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
        return False
    
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
    
    
        
