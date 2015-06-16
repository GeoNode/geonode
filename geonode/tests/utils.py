#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import urllib
import urllib2
import contextlib
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
            token = [
                x.value for x in cookies.cookiejar if x.name == 'csrftoken'][0]
        except IndexError:
            return False, "no csrftoken"

        params = dict(username=username, password=password,
                      this_is_the_login_form=True,
                      csrfmiddlewaretoken=token,
                      )
        encoded_params = urllib.urlencode(params)

        with contextlib.closing(opener.open(login_url, encoded_params)) as f:
            f.read()

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
    except urllib2.HTTPError as e:
        msg = ('The server couldn\'t fulfill the request. '
               'Error code: %s' % e.code)
        e.args = (msg,)
        raise
    except urllib2.URLError as e:
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
    assert isinstance(uploaded, Layer), msg
    msg = ('The layer does not have a valid name: %s' % uploaded.name)
    assert len(uploaded.name) > 0, msg
