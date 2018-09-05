# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from geonode.tests.base import GeoNodeBaseTestSupport

import contextlib
import copy
import urllib
import urllib2

from django.core.management import call_command
from django.db.models import signals
from django.core import mail
from django.conf import settings

from geonode.geoserver.signals import geoserver_post_save
from geonode.maps.models import Layer
from geonode.utils import set_attributes
from geonode.notifications_helper import has_notifications, notifications


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


class TestSetAttributes(GeoNodeBaseTestSupport):

    def setUp(self):
        super(TestSetAttributes, self).setUp()
        # Load users to log in as
        call_command('loaddata', 'people_data', verbosity=0)

    def test_set_attributes_creates_attributes(self):
        """ Test utility function set_attributes() which creates Attribute instances attached
            to a Layer instance.
        """
        # Creating a layer requires being logged in
        self.client.login(username='norman', password='norman')

        # Disconnect the geoserver-specific post_save signal attached to Layer creation.
        # The geoserver signal handler assumes things about the store where the Layer is placed.
        # this is a workaround.
        disconnected_post_save = signals.post_save.disconnect(geoserver_post_save, sender=Layer)

        # Create dummy layer to attach attributes to
        _l = Layer.objects.create(
            name='dummy_layer',
            bbox_x0=-180,
            bbox_x1=180,
            bbox_y0=-90,
            bbox_y1=90,
            srid='EPSG:4326')

        # Reconnect the signal if it was disconnected
        if disconnected_post_save:
            signals.post_save.connect(geoserver_post_save, sender=Layer)

        attribute_map = [
            ['id', 'Integer'],
            ['date', 'IntegerList'],
            ['enddate', 'Real'],
            ['date_as_date', 'xsd:dateTime'],
        ]

        # attribute_map gets modified as a side-effect of the call to set_attributes()
        expected_results = copy.deepcopy(attribute_map)

        # set attributes for resource
        set_attributes(_l, attribute_map)

        # 2 items in attribute_map should translate into 2 Attribute instances
        self.assertEquals(_l.attributes.count(), len(expected_results))

        # The name and type should be set as provided by attribute map
        for a in _l.attributes:
            self.assertIn([a.attribute, a.attribute_type], expected_results)


if has_notifications:
    import pickle
    import base64
    from pinax.notifications.tests import get_backend_id
    from pinax.notifications.engine import send_all
    from pinax.notifications.models import NoticeQueueBatch

    class NotificationsTestsHelper(GeoNodeBaseTestSupport):

        """
        Helper class for notification tests
        This provides:
         *
        """

        def setup_notifications_for(self, notifications_list, user):
            notices = []
            email_id = get_backend_id("email")
            obc = notifications.models.NoticeSetting.objects.create
            ont = notifications.models.NoticeType.objects.get

            for name, label, desc in notifications_list:
                n = obc(user=user,
                        notice_type=ont(label=name),
                        medium=email_id,
                        send=True
                        )
                notices.append(n)
            return notices

        def clear_notifications_queue(self):
            send_all()

        def check_notification_out(self, notification_name, user):
            """
            Return True if user received notification
            """
            # with queued notifications we can detect notification types easier
            if settings.PINAX_NOTIFICATIONS_QUEUE_ALL:
                self.assertTrue(NoticeQueueBatch.objects.all().count() > 0)

                user.noticesetting_set.get(notice_type__label=notification_name)
                # we're looking for specific notification type/user combination, which is probably
                # at the end

                for queued_batch in NoticeQueueBatch.objects.all():
                    notices = pickle.loads(base64.b64decode(queued_batch.pickled_data))
                    for user_id, label, extra_context, sender in notices:
                        if label == notification_name and user_id == user.pk:
                            return True

                # clear notifications queue
                send_all()
                return False
            else:
                send_all()
                # empty outbox:/
                if not mail.outbox:
                    return False

                msg = mail.outbox[-1]
                user.noticesetting_set.get(notice_type__label=notification_name)

                # unfortunatelly we can't use description check in subject, because subject is
                # generated from other template.
                # and notification.notice_type.description in msg.subject
                # last email should contain notification
                return user.email in msg.to
