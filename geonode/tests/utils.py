import os
import urllib, urllib2, cookielib
import contextlib
import tempfile
import zipfile

from geonode.maps.models import Layer

def get_web_page(url, username=None, password=None, login_url=None):
    """Get url page possible with username and password.
    """

    if login_url:
        # Login via a form
        cookies = urllib2.HTTPCookieProcessor()
        opener = urllib2.build_opener(cookies)
        urllib2.install_opener(opener)

        opener.open(login_url)

        try:
            token = [x.value for x in cookies.cookiejar if x.name == 'csrftoken'][0]
        except IndexError:
            return False, "no csrftoken"

        params = dict(username=username, password=password, \
            this_is_the_login_form=True,
            csrfmiddlewaretoken=token,
            )
        encoded_params = urllib.urlencode(params)

        with contextlib.closing(opener.open(login_url, encoded_params)) as f:
            html = f.read()

    elif username is not None:
        # Login using basic auth

        # Create password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        # create the handler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    try:
        pagehandle = urllib2.urlopen(url)
    except urllib2.HTTPError, e:
        msg = ('The server couldn\'t fulfill the request. '
                'Error code: %s' % e.code)
        e.args = (msg,)
        raise
    except urllib2.URLError, e:
        msg = 'Could not open URL "%s": %s' % (url, e)
        e.args = (msg,)
        raise
    else:
        page = pagehandle.read()

    return page

def check_layer(uploaded):
    """Verify if an object is a valid Layer.
    """
    msg = ('Was expecting layer object, got %s' % (type(uploaded)))
    assert type(uploaded) is Layer, msg
    msg = ('The layer does not have a valid name: %s' % uploaded.name)
    assert len(uploaded.name) > 0, msg

def download_and_unzip(url, username=None, password=None):
    """ Download a zip file from the specified URL and unzip it
    """

    temp_dir = tempfile.mkdtemp()
    name = os.path.join(temp_dir, 'temp.zip')
    print name
    content = get_web_page(url, username, password)
    FILE = open(name, 'wb')
    FILE.write(content)
    FILE.close()
    z = zipfile.ZipFile(name)
    for n in z.namelist():
        dest = os.path.join(temp_dir, n)
        destdir = os.path.dirname(dest)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        data = z.read(n)
        f = open(dest, 'w')
        f.write(data)
        f.close()
    z.close()
    os.unlink(name)
    return temp_dir
