import urllib, urllib2, cookielib
from datetime import date
from django.template import Context
from django.template.loader import get_template
from xml.dom import minidom
from xml.etree.ElementTree import XML

class Catalog(object):

    def __init__(self, base, user, password):
        self.base = base
        self.user = user
        self.password = password

    def login(self):
        url = "%ssrv/en/xml.user.login" % self.base
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        post = urllib.urlencode({
            "username": self.user,
            "password": self.password
        })
        request = urllib2.Request(url, post, headers)
        response = urllib2.urlopen(request)
        body = response.read()
        dom = minidom.parseString(body)
        assert dom.childNodes[0].nodeName == 'ok', "GeoNetwork login failed!"

        self.cookies = cookielib.CookieJar()
        self.cookies.extract_cookies(response, request)
        cookie_handler = urllib2.HTTPCookieProcessor(self.cookies)
        redirect_handler = urllib2.HTTPRedirectHandler()
        self.opener = urllib2.build_opener(redirect_handler, cookie_handler)

    def logout(self):
        url = "%ssrv/en/xml.user.logout" % self.base
        request = urllib2.Request(url)
        response = self.opener.open(request)

    def get_by_uuid(self, uuid):
        pass

    def create_from_layer(self, layer):
        tpl = get_template("maps/csw/transaction_insert.xml")
        now = date.today()
        ctx = Context({
            'layer': layer,
            'now': now,
            'uuid': layer.uuid
        })
        md_doc = tpl.render(ctx)

        url = "%ssrv/en/csw" % self.base
        headers = {
            "Content-Type": "application/xml",
            "Accept": "text/plain"
        }
        request = urllib2.Request(url, md_doc, headers)
        response = self.urlopen(request)

        # print layer.uuid
        # print response.read()
        # TODO: Parse response, check for error report


        # Turn on the "view" permission (aka publish) for
        # the "all" group in GeoNetwork so that the layer
        # will be searchable via CSW without admin login.
        self.set_metadata_priv(layer.uuid, "all", "view", True)
        
        return self.base + "srv/en/csw?" + urllib.urlencode({
            "request": "GetRecordById",
            "service": "CSW",
            "version": "2.0.2",
            "OutputSchema": "http://www.isotc211.org/2005/gmd",
            "ElementSetName": "full",
            "id": layer.uuid
        })

    def update_from_layer(self, record, layer):
        pass

    def set_metadata_priv(self, uuid, group, operation, enabled):
        """
        set the geonetwork privilege 'operation' to the value 
        of 'enabled' for the group 'group' on the metadata
        item identified by 'uuid'
        """
        
        # XXX This is a fairly ugly workaround that makes 
        # requests similar to those made by the GeoNetwork
        # admin based on the recommendation here: 
        # http://bit.ly/ccVEU7
        
        get_dbid_url = self.base + 'srv/en/portal.search.present?' + urllib.urlencode({'uuid': uuid})
        get_groups_url = self.base + "srv/en/xml.info?" + urllib.urlencode({'type': 'groups'})
        get_ops_url = self.base + "srv/en/xml.info?" + urllib.urlencode({'type': 'operations'})
    
    
        # get the id of the data.
        request = urllib2.Request(get_dbid_url)
        response = self.urlopen(request)
        doc = XML(response.read())
        data_dbid = doc.find('metadata/{http://www.fao.org/geonetwork}info/id').text

        # get the id of the group.
        request = urllib2.Request(get_groups_url)
        response = self.urlopen(request)
        doc = XML(response.read())
        group_id = None
        for gp in doc.findall('groups/group'):
            if gp.find('name').text.lower() == group.lower():
                group_id = gp.attrib['id']
        if group_id is None:
            raise Exception('Unable to locate geonetwork group "%s"' % group)
        
        # get the id of the operation    
        request = urllib2.Request(get_ops_url)
        response = self.urlopen(request)
        doc = XML(response.read())
        operation_id = None
        for op in doc.findall('operations/operation'):
            if op.find('name').text.lower() == operation.lower():
                operation_id = op.attrib['id']
        if operation_id is None:
            raise Exception('Unable to locate geonetwork privilege "%s"' % operation)

        # update the privilege 
        update_privs_url = self.base + "srv/en/metadata.admin?" + urllib.urlencode({
            "id": data_dbid, # "uuid": layer.uuid, # you can say this instead in newer versions of GN 
            "_%s_%s" % (group_id, operation_id): "on", # All: Publish=on
        })
        request = urllib2.Request(update_privs_url)
        response = self.urlopen(request)

        # TODO: check for error report

    def urlopen(self, request):
        if self.opener is None:
            return urllib2.urlopen(request)
        else:
            return self.opener.open(request)
