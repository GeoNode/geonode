import urllib, urllib2, cookielib
from datetime import date
from django.template import Context
from django.template.loader import get_template
from xml.dom import minidom

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

        if self.opener is None:
            response = urllib2.urlopen(request)
        else:
            response = self.opener.open(request)

        print layer.uuid
        print response.read()
#TODO: Parse response, check for error report

    def update_from_layer(self, record, layer):
        pass
