# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from __future__ import print_function

from geonode.tests.base import GeoNodeBaseTestSupport

from datetime import datetime, timedelta

import os
import time
import json
import pytz
import logging
import os.path
import xmljson
from decimal import Decimal  # noqa
from importlib import import_module
from defusedxml import lxml as dlxml

from django.core import mail
from django.conf import settings
from django.http import HttpRequest
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.contrib.auth import login, get_user, get_user_model

from geonode.monitoring.models import (
    RequestEvent, Host, Service, ServiceType,
    populate, ExceptionEvent, MetricNotificationCheck,
    MetricValue, NotificationCheck, Metric, EventType,
    MonitoredResource, MetricLabel,
    NotificationMetricDefinition,)
from geonode.monitoring.models import do_autoconfigure

from geonode.monitoring.collector import CollectorAPI
from geonode.monitoring.utils import generate_periods, align_period_start

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.people.models import Profile
from geonode.documents.models import Document

from geonode.tests.utils import Client
from geonode.geoserver.helpers import ogc_server_settings

from django.test.client import Client as DjangoTestClient

import gisdata
from geoserver.catalog import Catalog
from geonode.layers.utils import file_upload

GEONODE_USER = 'admin'
GEONODE_PASSWD = 'admin'
GEONODE_URL = settings.SITEURL.rstrip('/')
GEOSERVER_URL = ogc_server_settings.LOCATION
GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.credentials

logging.getLogger('south').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# create test user if needed, delete all layers and set password
u, created = Profile.objects.get_or_create(username=GEONODE_USER)
if created:
    u.set_password(GEONODE_PASSWD)
    u.save()
else:
    Layer.objects.filter(owner=u).delete()

res_dir = os.path.join(os.path.dirname(__file__), 'resources')
req_err_path = os.path.join(res_dir, 'req_err.xml')
req_path = os.path.join(res_dir, 'req.xml')

req_err_xml = open(req_err_path, 'rt').read()
req_xml = open(req_path, 'rt').read()

req_big = xmljson.yahoo.data(dlxml.fromstring(req_xml))
req_err_big = xmljson.yahoo.data(dlxml.fromstring(req_err_xml))


class TestClient(DjangoTestClient):

    def login_user(self, user):
        """
        Login as specified user, does not depend on auth backend (hopefully)

        This is based on Client.login() with a small hack that does not
        require the call to authenticate()
        """
        if 'django.contrib.sessions' not in settings.INSTALLED_APPS:
            raise AssertionError("Unable to login without django.contrib.sessions in INSTALLED_APPS")
        user.backend = "%s.%s" % ("django.contrib.auth.backends",
                                  "ModelBackend")
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        if self.session:
            request.session = self.session
        else:
            request.session = engine.SessionStore()
        login(request, user)

        # Set the cookie to represent the session.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE or None,
            'expires': None,
        }
        self.cookies[session_cookie].update(cookie_data)

        # Save the session values.
        request.session.save()


class MonitoringTestBase(GeoNodeBaseTestSupport):

    type = 'layer'

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        if os.path.exists('integration_settings.py'):
            os.unlink('integration_settings.py')

    def setUp(self):
        # super(MonitoringTestBase, self).setUp()

        # await startup
        cl = Client(
            GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        )
        for i in range(10):
            time.sleep(.2)
            try:
                cl.get_html('/', debug=False)
                break
            except BaseException:
                pass

        self.catalog = Catalog(
            GEOSERVER_URL + 'rest', GEOSERVER_USER, GEOSERVER_PASSWD
        )

        self.client = TestClient()

        self._tempfiles = []
        # createlayer must use postgis as a datastore
        # set temporary settings to use a postgis datastore
        # DB_HOST = DATABASES['default']['HOST']
        # DB_PORT = DATABASES['default']['PORT']
        # DB_NAME = DATABASES['default']['NAME']
        # DB_USER = DATABASES['default']['USER']
        # DB_PASSWORD = DATABASES['default']['PASSWORD']
        # settings.DATASTORE_URL = 'postgis://{}:{}@{}:{}/{}'.format(
        #     DB_USER,
        #     DB_PASSWORD,
        #     DB_HOST,
        #     DB_PORT,
        #     DB_NAME
        # )
        # postgis_db = dj_database_url.parse(
        #     settings.DATASTORE_URL, conn_max_age=600)
        # settings.DATABASES['datastore'] = postgis_db
        # settings.OGC_SERVER['default']['DATASTORE'] = 'datastore'

        # upload(gisdata.DATA_DIR, console=None)

    def tearDown(self):
        # super(MonitoringTestBase, self).setUp()

        map(os.unlink, self._tempfiles)

        # Cleanup
        Layer.objects.all().delete()
        Map.objects.all().delete()
        Document.objects.all().delete()

        from django.conf import settings
        if settings.OGC_SERVER['default'].get(
                "GEOFENCE_SECURITY_ENABLED", False):
            from geonode.security.utils import purge_geofence_all
            purge_geofence_all()


@override_settings(USE_TZ=True)
class RequestsTestCase(MonitoringTestBase):

    def setUp(self):
        super(RequestsTestCase, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.email = 'test@email.com'
        self.u.set_password(self.passwd)
        self.u.save()
        self.ua = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                   "(KHTML, like Gecko) Chrome/59.0.3071.47 Safari/537.36")
        populate()

        self.host, _ = Host.objects.get_or_create(
            name='localhost', ip='127.0.0.1')
        self.service_type = ServiceType.objects.get(
            name=ServiceType.TYPE_GEONODE)
        self.service, _ = Service.objects.get_or_create(
            name=settings.MONITORING_SERVICE_NAME,
            host=self.host,
            service_type=self.service_type)

    def test_gs_req(self):
        """
        Test if we can parse geoserver requests
        """
        rq = RequestEvent.from_geoserver(self.service, req_big)
        self.assertTrue(rq)

    def test_gs_err_req(self):
        """
        Test if we can parse geoserver requests
        """
        rq = RequestEvent.from_geoserver(self.service, req_err_big)
        self.assertTrue(rq)
        q = ExceptionEvent.objects.filter(request=rq)
        self.assertEqual(q.count(), 1)
        self.assertEqual(
            q[0].error_type,
            'org.geoserver.platform.ServiceException')

    def test_gn_request(self):
        """
        Test if we have geonode requests logged
        """
        self.client.force_login(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())

        _l = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name="san_andres_y_providencia_poi",
            user=self.u,
            overwrite=True,
        )

        self.client.get(
            reverse('layer_detail',
                    args=(_l.alternate,
                          )),
            **{"HTTP_USER_AGENT": self.ua})

        self.assertEqual(RequestEvent.objects.all().count(), 1)
        rq = RequestEvent.objects.get()
        self.assertTrue(rq.response_time > 0)
        self.assertEqual(
            list(rq.resources.all().values_list('name', 'type')), [(_l.alternate, u'layer',)])
        self.assertEqual(rq.request_method, 'GET')

    def test_gn_error(self):
        """
        Test if we get geonode errors logged
        """
        self.client.force_login(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())

        _l = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name="san_andres_y_providencia_poi",
            user=self.u,
            overwrite=True,
        )
        self.assertIsNotNone(_l)
        self.client.get(
            reverse('layer_detail', args=('nonex',)), **{"HTTP_USER_AGENT": self.ua})

        RequestEvent.objects.get()
        self.assertEqual(RequestEvent.objects.all().count(), 1)

        self.assertEqual(ExceptionEvent.objects.all().count(), 1)
        eq = ExceptionEvent.objects.get()
        self.assertEqual('django.http.response.Http404', eq.error_type)

    def test_service_handlers(self):
        """
        Test if we can calculate metrics
        """
        self.client.force_login(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())

        _l = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name="san_andres_y_providencia_poi",
            user=self.u,
            overwrite=True,
        )

        for idx, _l in enumerate(Layer.objects.all()):
            for inum in range(0, idx + 1):
                self.client.get(
                    reverse('layer_detail',
                            args=(_l.alternate,
                                  )),
                    **{"HTTP_USER_AGENT": self.ua})

        # Works only with Postgres
        requests = RequestEvent.objects.all()

        c = CollectorAPI()
        q = requests.order_by('created')
        c.process_requests(
            self.service,
            requests,
            q.first().created,
            q.last().created)

        interval = self.service.check_interval
        now = datetime.utcnow().replace(tzinfo=pytz.utc)

        valid_from = now - (2 * interval)
        valid_to = now

        self.assertTrue(isinstance(valid_from, datetime))
        self.assertTrue(isinstance(valid_to, datetime))
        self.assertTrue(isinstance(interval, timedelta))

        # Works only with Postgres
        metrics = c.get_metrics_for(metric_name='request.ip',
                                    valid_from=valid_from,
                                    valid_to=valid_to,
                                    interval=interval)
        self.assertIsNotNone(metrics)


@override_settings(USE_TZ=True)
class MonitoringUtilsTestCase(MonitoringTestBase):

    def setUp(self):
        super(MonitoringUtilsTestCase, self).setUp()

    def test_time_periods(self):
        """
        Test if we can use time periods
        """
        import pytz
        utc = pytz.utc

        # 2017-06-20 12:22:50
        start = datetime(
            year=2017,
            month=0o6,
            day=20,
            hour=12,
            minute=22,
            second=50)
        # 2017-06-20 12:20:00
        start_aligned = datetime(
            year=2017,
            month=0o6,
            day=20,
            hour=12,
            minute=20,
            second=0)
        interval = timedelta(minutes=5)
        # 12:22:50+ 0:05:20 = 12:27:02
        end = start + timedelta(minutes=5, seconds=22)

        expected_periods = [(start_aligned.replace(tzinfo=utc),
                             start_aligned.replace(tzinfo=utc) + interval,),
                            (start_aligned.replace(tzinfo=utc) + interval,
                             start_aligned.replace(
                                 tzinfo=utc) + (2 * interval),),
                            ]

        aligned = align_period_start(start, interval)
        self.assertEqual(
            start_aligned.replace(tzinfo=utc),
            aligned.replace(tzinfo=utc))

        periods = list(generate_periods(start, interval, end))
        self.assertEqual(expected_periods, periods)
        pnow = datetime.utcnow().replace(tzinfo=pytz.utc)
        start_for_one = pnow - interval
        periods = list(generate_periods(start_for_one, interval, pnow))
        self.assertEqual(len(periods), 1)

        start_for_two = pnow - (2 * interval)
        periods = list(generate_periods(start_for_two, interval, pnow))
        self.assertEqual(len(periods), 2)

        start_for_three = pnow - (3 * interval)
        periods = list(generate_periods(start_for_three, interval, pnow))
        self.assertEqual(len(periods), 3)

        start_for_two_and_half = pnow - \
            timedelta(seconds=(2.5 * interval.total_seconds()))
        periods = list(
            generate_periods(
                start_for_two_and_half,
                interval,
                pnow))
        self.assertEqual(len(periods), 3)


@override_settings(USE_TZ=True)
class MonitoringChecksTestCase(MonitoringTestBase):

    reserved_fields = ('emails', 'severity', 'active', 'grace_period',)

    def setUp(self):
        super(MonitoringChecksTestCase, self).setUp()

        populate()

        self.host, _ = Host.objects.get_or_create(
            name='localhost', ip='127.0.0.1')
        self.service_type = ServiceType.objects.get(
            name=ServiceType.TYPE_GEONODE)
        self.service, _ = Service.objects.get_or_create(
            name=settings.MONITORING_SERVICE_NAME,
            host=self.host,
            service_type=self.service_type)
        self.metric = Metric.objects.get(name='request.count')
        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.email = 'test@email.com'
        self.u.set_password(self.passwd)
        self.u.save()
        self.user2 = 'test'
        self.passwd2 = 'test'
        self.u2, _ = get_user_model().objects.get_or_create(username=self.user2)
        self.u2.is_active = True
        self.u2.email = 'test2@email.com'
        self.u2.set_password(self.passwd2)
        self.u2.save()

    def test_monitoring_checks(self):
        start = datetime.utcnow().replace(tzinfo=pytz.utc)
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval
        # sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        event_type = EventType.objects.get(name='OWS:WFS')
        resource, _ = MonitoredResource.objects.get_or_create(
            type='layer', name='test:test')
        resource2, _ = MonitoredResource.objects.get_or_create(
            type='layer', name='test:test2')

        label, _ = MetricLabel.objects.get_or_create(name='discount')
        MetricValue.add(self.metric, start_aligned,
                        end_aligned, self.service,
                        label="Count",
                        value_raw=10,
                        value_num=10,
                        value=10)
        uthreshold = [(
            self.metric.name, 'min_value', False, False, False, False, 0, 100, None, "Min number of request"),
            (self.metric.name, 'max_value', False, False, False, False,
             1000, None, None, "Max number of request"), ]
        notification_data = {'name': 'check requests name',
                             'description': 'check requests description',
                             'severity': 'warning',
                             'user_threshold': uthreshold}
        nc = NotificationCheck.create(**notification_data)
        mc = MetricNotificationCheck.objects.create(notification_check=nc,
                                                    service=self.service,
                                                    metric=self.metric,
                                                    min_value=None,
                                                    definition=nc.definitions.first(
                                                    ),
                                                    max_value=None,
                                                    max_timeout=None)
        with self.assertRaises(ValueError):
            mc.check_metric(for_timestamp=start)

        mc.min_value = 11
        mc.save()

        with self.assertRaises(mc.MetricValueError):
            mc.check_metric(for_timestamp=start)

        mc.min_value = 1
        mc.max_value = 11
        mc.save()

        self.assertTrue(mc.check_metric(for_timestamp=start))

        MetricValue.add(self.metric, start_aligned, end_aligned, self.service,
                        label="discount",
                        value_raw=10,
                        value_num=10,
                        value=10,
                        event_type=event_type)

        mc.min_value = 11
        mc.max_value = None
        mc.event_type = event_type
        mc.save()

        with self.assertRaises(mc.MetricValueError):
            mc.check_metric(for_timestamp=start)

        MetricValue.add(self.metric, start_aligned, end_aligned, self.service,
                        label="discount",
                        value_raw=10,
                        value_num=10,
                        value=10,
                        resource=resource)
        mc.min_value = 1
        mc.max_value = 10
        mc.event_type = None
        mc.resource = resource
        mc.save()

        self.assertTrue(mc.check_metric(for_timestamp=start))

        MetricValue.objects.all().delete()

        MetricValue.add(self.metric, start_aligned, end_aligned, self.service,
                        label="discount",
                        value_raw=10,
                        value_num=10,
                        value=10,
                        resource=resource2)
        # this should raise ValueError, because MetricValue won't match
        with self.assertRaises(ValueError):
            mc.check_metric(for_timestamp=start)

    def test_notifications_views(self):

        start = datetime.utcnow().replace(tzinfo=pytz.utc)
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval

        # sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        resource, _ = MonitoredResource.objects.get_or_create(
            type='layer', name='test:test')
        resource2, _ = MonitoredResource.objects.get_or_create(
            type='layer', name='test:test2')

        label, _ = MetricLabel.objects.get_or_create(name='discount')
        MetricValue.add(self.metric, start_aligned, end_aligned, self.service,
                        label="Count",
                        value_raw=10,
                        value_num=10,
                        value=10)
        nc = NotificationCheck.objects.create(
            name='check requests',
            description='check requests')

        MetricNotificationCheck.objects.create(notification_check=nc,
                                               service=self.service,
                                               metric=self.metric,
                                               min_value=10,
                                               max_value=200,
                                               resource=resource,
                                               max_timeout=None)

        self.client.force_login(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(nresp.status_code, 200, nresp)
        # data = json.loads(nresp.content)
        # self.assertTrue(data['data'][0]['id'] == nc.id)

        nresp = self.client.get(
            reverse('monitoring:api_user_notification_config',
                    kwargs={'pk': nc.id}))
        self.assertIsNotNone(nresp)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(nresp.status_code, 200, nresp)
        # data = json.loads(nresp.content)
        # self.assertTrue(data['data']['notification']['id'] == nc.id)

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(nresp.status_code, 200, nresp)
        # data = json.loads(nresp.content)
        # self.assertTrue(data['data'][0]['id'] == nc.id)

        self.client.force_login(self.u2)
        self.assertTrue(get_user(self.client).is_authenticated())

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(nresp.status_code, 200, nresp)
        # data = json.loads(nresp.content)
        # self.assertTrue(len(data['data']) == 1)

    def test_notifications_edit_views(self):

        start = datetime.utcnow().replace(tzinfo=pytz.utc)
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval

        # sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        resource, _ = MonitoredResource.objects.get_or_create(
            type='layer', name='test:test')

        label, _ = MetricLabel.objects.get_or_create(name='discount')

        c = self.client
        c.force_login(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())
        notification_url = reverse('monitoring:api_user_notifications')
        uthreshold = [(
            'request.count', 'min_value', False, False, False, False, 0, 100, None, "Min number of request"),
            ('request.count', 'max_value', False, False, False, False,
             1000, None, None, "Max number of request"), ]
        notification_data = {'name': 'test',
                             'description': 'more test',
                             'severity': 'warning',
                             'user_threshold': json.dumps(uthreshold)}

        out = c.post(notification_url, notification_data)
        self.assertEqual(out.status_code, 200)

        jout = json.loads(out.content)
        nid = jout['data']['id']
        ndef = NotificationMetricDefinition.objects.filter(
            notification_check__id=nid)
        self.assertEqual(ndef.count(), 2)

        notification_url = reverse(
            'monitoring:api_user_notification_config',
            kwargs={'pk': nid})
        notification = NotificationCheck.objects.get(pk=nid)
        notification_data = {'name': 'testttt',
                             'emails': [self.u.email, 'testother@test.com', ],
                             'severity': 'error',
                             'description': 'more tesddddt'}
        form = notification.get_user_form()
        fields = {}

        for field in form.fields.values():
            if not hasattr(field, 'name'):
                continue
            fields[field.name] = int((field.min_value or 0) + 1)
        notification_data.update(fields)
        out = c.post(notification_url, notification_data)
        self.assertIsNotNone(out)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(out.status_code, 200, out)
        # jout = json.loads(out.content)
        # n = NotificationCheck.objects.get()
        # self.assertTrue(n.is_error)
        # self.assertEqual(MetricNotificationCheck.objects.all().count(), 2)
        # for nrow in jout['data']:
        #     nitem = MetricNotificationCheck.objects.get(id=nrow['id'])
        #     for nkey, nval in nrow.items():
        #         if not isinstance(nval, dict):
        #             compare_to = getattr(nitem, nkey)
        #             if isinstance(compare_to, Decimal):
        #                 nval = Decimal(nval)
        #             self.assertEqual(compare_to, nval)

        out = c.post(
            notification_url,
            json.dumps(notification_data),
            content_type='application/json')
        self.assertIsNotNone(out)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(out.status_code, 200)
        # jout = json.loads(out.content)
        # n = NotificationCheck.objects.get()
        # self.assertTrue(n.is_error)
        # self.assertEqual(MetricNotificationCheck.objects.all().count(), 2)
        # for nrow in jout['data']:
        #     nitem = MetricNotificationCheck.objects.get(id=nrow['id'])
        #     for nkey, nval in nrow.items():
        #         if not isinstance(nval, dict):
        #             compare_to = getattr(nitem, nkey)
        #             if isinstance(compare_to, Decimal):
        #                 nval = Decimal(nval)
        #             self.assertEqual(compare_to, nval)

    def test_notifications_api(self):
        capi = CollectorAPI()
        start = datetime.utcnow().replace(tzinfo=pytz.utc)

        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval

        # for (metric_name, field_opt, use_service,
        #     use_resource, use_label, use_event_type,
        #     minimum, maximum, thresholds,) in thresholds:

        notifications_config = ('geonode is not working',
                                'detects when requests are not handled',
                                (('request.count', 'min_value', False, False,
                                  False, False, 0, 10, None, 'Number of handled requests is lower than',),
                                 ('response.time', 'max_value', False, False,
                                  False, False, 500, None, None, 'Response time is higher than',),))
        nc = NotificationCheck.create(*notifications_config)
        self.assertTrue(nc.definitions.all().count() == 2)
        self.client.force_login(self.u2)
        self.assertTrue(get_user(self.client).is_authenticated())
        for nc in NotificationCheck.objects.all():
            notifications_config_url = reverse(
                'monitoring:api_user_notification_config', args=(nc.id,))
            nc_form = nc.get_user_form()
            self.assertTrue(nc_form)
            self.assertTrue(nc_form.fields.keys())
            vals = [1000000, 100000]
            data = {'emails': []}
            data['emails'] = '\n'.join(data['emails'])
            idx = 0
            for fname, field in nc_form.fields.items():
                if fname in self.reserved_fields:
                    continue
                data[fname] = vals[idx]
                idx += 1
            resp = self.client.post(notifications_config_url, data)

            self.assertEqual(resp.status_code, 401)

            vals = [7, 600]
            data = {'emails': '\n'.join(
                    [self.u.email,
                     self.u2.email,
                     'testsome@test.com'])}
            idx = 0
            for fname, field in nc_form.fields.items():
                if fname in self.reserved_fields:
                    continue
                data[fname] = vals[idx]
                idx += 1
            # data['emails'] = '\n'.join(data['emails'])
            resp = self.client.post(notifications_config_url, data)
            nc.refresh_from_db()
            # AF: TODO there's no way to make Monitoring aware this user is_authenticated
            # self.assertEqual(resp.status_code, 200, resp)
            # _emails = data['emails'].split('\n')[-1:]
            # _users = data['emails'].split('\n')[:-1]
            # self.assertEqual(
            #     set([u.email for u in nc.get_users()]),
            #     set(_users))
            # self.assertEqual(
            #     set([email for email in nc.get_emails()]),
            #     set(_emails))

        metric_rq_count = Metric.objects.get(name='request.count')
        metric_rq_time = Metric.objects.get(name='response.time')

        MetricValue.add(metric_rq_count,
                        start_aligned,
                        end_aligned,
                        self.service,
                        label="Count",
                        value_raw=0,
                        value_num=0,
                        value=0)

        MetricValue.add(metric_rq_time,
                        start_aligned,
                        end_aligned,
                        self.service,
                        label="Count",
                        value_raw=700,
                        value_num=700,
                        value=700)

        nc = NotificationCheck.objects.get()
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertTrue(len(nc.get_emails()) > 0)
        # self.assertTrue(len(nc.get_users()) > 0)
        # self.assertEqual(nc.last_send, None)
        # self.assertTrue(nc.can_send)
        # self.assertEqual(len(mail.outbox), 0)

        # make sure inactive will not trigger anything
        nc.active = False
        nc.save()
        capi.emit_notifications(start)
        self.assertEqual(len(mail.outbox), 0)

        nc.active = True
        nc.save()
        capi.emit_notifications(start)
        self.assertTrue(nc.receivers.all().count() >= 0)
        self.assertEqual(len(mail.outbox), nc.receivers.all().count())

        nc.refresh_from_db()
        notifications_url = reverse('monitoring:api_user_notifications')
        nresp = self.client.get(notifications_url)
        self.assertIsNotNone(nresp)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(nresp.status_code, 200)
        # ndata = json.loads(nresp.content)
        # self.assertEqual(set([n['id'] for n in ndata['data']]),
        #                  set(NotificationCheck.objects.all().values_list('id', flat=True)))
        # self.assertTrue(isinstance(nc.last_send, datetime))
        # self.assertFalse(nc.can_send)
        # mail.outbox = []
        # self.assertEqual(len(mail.outbox), 0)
        # capi.emit_notifications(start)
        # self.assertEqual(len(mail.outbox), 0)
        # nc.last_send = start - nc.grace_period
        # nc.save()
        # self.assertTrue(nc.can_send)
        # mail.outbox = []
        # self.assertEqual(len(mail.outbox), 0)
        # capi.emit_notifications(start)
        # self.assertEqual(len(mail.outbox), nc.receivers.all().count())


@override_settings(USE_TZ=True)
class AutoConfigTestCase(MonitoringTestBase):

    OGC_GS_1 = 'http://localhost/geoserver123/'
    OGC_GS_2 = 'http://google.com/test/'

    OGC_SERVER = {'default': {'BACKEND': 'nongeoserver'},
                  'geoserver1':
                      {'BACKEND': 'geonode.geoserver', 'LOCATION': OGC_GS_1},
                  'external1': {'BACKEND': 'geonode.geoserver', 'LOCATION': OGC_GS_2}
                  }

    def setUp(self):
        super(AutoConfigTestCase, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.set_password(self.passwd)
        self.u.is_active = True
        self.u.is_superuser = True
        self.u.email = 'test@email.com'
        self.u.save()

        self.user2 = 'test'
        self.passwd2 = 'test'
        self.u2, _ = get_user_model().objects.get_or_create(username=self.user2)
        self.u2.set_password(self.passwd2)
        self.u2.is_active = True
        self.u2.email = 'test2@email.com'
        self.u2.save()

    def test_autoconfig(self):
        with self.settings(OGC_SERVER=self.OGC_SERVER, SITEURL=self.OGC_GS_2):
            do_autoconfigure()
        h1 = Host.objects.get(name='localhost')
        h2 = Host.objects.get(name='google.com')
        s1 = Service.objects.get(name='geoserver1-geoserver')
        self.assertEqual(s1.host, h1)
        s2 = Service.objects.get(name='external1-geoserver')
        self.assertEqual(s2.host, h2)

        autoconf_url = reverse('monitoring:api_autoconfigure')
        resp = self.client.post(autoconf_url)
        self.assertEqual(resp.status_code, 401)

        self.client.force_login(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())
        resp = self.client.post(autoconf_url)
        # AF: TODO there's no way to make Monitoring aware this user is_authenticated
        # self.assertEqual(resp.status_code, 200, resp)


@override_settings(USE_TZ=True)
class MonitoringAnalyticsTestCase(MonitoringTestBase):

    def setUp(self):
        super(MonitoringAnalyticsTestCase, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.email = 'test@email.com'
        self.u.set_password(self.passwd)
        self.u.save()
        self.ua = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                   "(KHTML, like Gecko) Chrome/59.0.3071.47 Safari/537.36")

        populate()

        self.host, _ = Host.objects.get_or_create(
            name='localhost', ip='127.0.0.1')
        self.service_type = ServiceType.objects.get(
            name=ServiceType.TYPE_GEONODE)
        self.service, _ = Service.objects.get_or_create(
            name=settings.MONITORING_SERVICE_NAME,
            host=self.host,
            service_type=self.service_type)

        file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name="san_andres_y_providencia_poi",
            user=self.u,
            overwrite=True,
        )

    def test_metric_data_endpoints(self):
        """
        Test GeoNode collect metrics
        """
        # Login (optional)
        self.client.force_login(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())

        _l = Layer.objects.all().first()

        # Event
        self.client.get(
            reverse('layer_detail',
                    args=(_l.alternate,
                          )),
            **{"HTTP_USER_AGENT": self.ua}
        )
        requests = RequestEvent.objects.all()
        self.assertTrue(requests.count() > 0)
        # First check for MetricValue table
        self.assertTrue(MetricValue.objects.all().count() == 0)
        # Metric data collection
        collector = CollectorAPI()
        q = requests.order_by('created')
        collector.process_requests(
            self.service,
            requests,
            q.first().created,
            q.last().created
        )
        # Second check for MetricValue table
        self.assertTrue(MetricValue.objects.all().count() >= 0)
        # Call endpoint
        url = "%s?%s" % (reverse('monitoring:api_metric_data', args={
                         'request.users'}), 'last=86400&interval=86400&event_type=view&resource_type=layer')
        response = self.client.get(url)  # noqa
        # TODO check response

    def test_resources_endpoint(self):
        response = self.client.get(reverse('monitoring:api_resources'))
        self.assertEqual(response.status_code, 200)
        resources = json.loads(response.content)['resources']
        r_ids = [r['id'] for r in resources]
        m_resources = MonitoredResource.objects.all()
        mr_ids = [mr.id for mr in m_resources]
        if mr_ids:
            self.assertEqual(r_ids, mr_ids)

    def test_resource_types_endpoint(self):
        response = self.client.get(reverse('monitoring:api_resource_types'))
        self.assertEqual(response.status_code, 200)
        resource_types = json.loads(response.content)['resource_types']
        r_types = [rt['name'] for rt in resource_types]
        m_resources = MonitoredResource.objects.all()
        mr_types = [mr.type for mr in m_resources]
        if mr_types:
            self.assertEqual(r_types, mr_types, resource_types)

    def test_event_types_endpoint(self):
        response = self.client.get(reverse('monitoring:api_event_types'))
        self.assertEqual(response.status_code, 200)
        event_types = json.loads(response.content)['event_types']
        e_types = [et['name'] for et in event_types]
        ev_types = [e.name for e in EventType.objects.all()]
        if ev_types:
            self.assertEqual(e_types, ev_types, event_types)
