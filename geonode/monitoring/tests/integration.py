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

from geonode.tests.base import GeoNodeLiveTestSupport

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
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.core.management import call_command
from django.contrib.auth import get_user, get_user_model

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

from django.test.client import FakePayload, Client as DjangoTestClient

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

    def _base_environ(self, **request):
        """
        The base environment for a request.
        """
        # This is a minimal valid WSGI environ dictionary, plus:
        # - HTTP_COOKIE: for cookie support,
        # - REMOTE_ADDR: often useful, see #8551.
        # See https://www.python.org/dev/peps/pep-3333/#environ-variables
        environ = {
            'HTTP_COOKIE': '; '.join(sorted(
                '%s=%s' % (morsel.key, morsel.coded_value)
                for morsel in self.cookies.values()
            )),
            'PATH_INFO': str('/'),
            'REMOTE_ADDR': str('127.0.0.1'),
            'REQUEST_METHOD': str('GET'),
            'SCRIPT_NAME': str(''),
            'SERVER_NAME': str('testserver'),
            'SERVER_PORT': str('80'),
            'SERVER_PROTOCOL': str('HTTP/1.1'),
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': str('http'),
            'wsgi.input': FakePayload(b''),
            'wsgi.errors': self.errors,
            'wsgi.multiprocess': True,
            'wsgi.multithread': False,
            'wsgi.run_once': False,
        }
        environ.update(self.defaults)
        environ.update(request)
        return environ

    @property
    def session(self):
        if not hasattr(self, "_persisted_session"):
            engine = import_module(settings.SESSION_ENGINE)
            self._persisted_session = engine.SessionStore("persistent")
        return self._persisted_session

    def login_user(self, user):
        """
        Login as specified user, does not depend on auth backend (hopefully)

        This is based on Client.login() with a small hack that does not
        require the call to authenticate()
        """
        if 'django.contrib.sessions' not in settings.INSTALLED_APPS:
            raise AssertionError("Unable to login without django.contrib.sessions in INSTALLED_APPS")
        user.backend = "%s.%s" % ("django.contrib.auth.backends", "ModelBackend")

        # Login
        self.force_login(user, backend=user.backend)


class MonitoringTestBase(GeoNodeLiveTestSupport):

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

        self.client = TestClient(REMOTE_ADDR='127.0.0.1')

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
        self.client.login_user(self.u)
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
        self.client.login_user(self.u)
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
        self.client.login_user(self.u)
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

        self.client.login_user(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(nresp.content)
        self.assertTrue(data['data'][0]['id'] == nc.id)

        nresp = self.client.get(
            reverse('monitoring:api_user_notification_config',
                    kwargs={'pk': nc.id}))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(nresp.content)
        self.assertTrue(data['data']['notification']['id'] == nc.id)

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(nresp.content)
        self.assertTrue(data['data'][0]['id'] == nc.id)

        self.client.login_user(self.u2)
        self.assertTrue(get_user(self.client).is_authenticated())

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(nresp.content)
        self.assertTrue(len(data['data']) == 1)

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
        c.login_user(self.u)
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
        self.assertEqual(out.status_code, 200, out)
        jout = json.loads(out.content)
        n = NotificationCheck.objects.get()
        self.assertTrue(n.is_error)
        self.assertEqual(MetricNotificationCheck.objects.all().count(), 2)
        for nrow in jout['data']:
            nitem = MetricNotificationCheck.objects.get(id=nrow['id'])
            for nkey, nval in nrow.items():
                if not isinstance(nval, dict):
                    compare_to = getattr(nitem, nkey)
                    if isinstance(compare_to, Decimal):
                        nval = Decimal(nval)
                    self.assertEqual(compare_to, nval)

        out = c.post(
            notification_url,
            json.dumps(notification_data),
            content_type='application/json')
        self.assertIsNotNone(out)
        self.assertEqual(out.status_code, 200)
        jout = json.loads(out.content)
        n = NotificationCheck.objects.get()
        self.assertTrue(n.is_error)
        self.assertEqual(MetricNotificationCheck.objects.all().count(), 2)
        for nrow in jout['data']:
            nitem = MetricNotificationCheck.objects.get(id=nrow['id'])
            for nkey, nval in nrow.items():
                if not isinstance(nval, dict):
                    compare_to = getattr(nitem, nkey)
                    if isinstance(compare_to, Decimal):
                        nval = Decimal(nval)
                    self.assertEqual(compare_to, nval)

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
        self.client.login_user(self.u2)
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

            self.assertEqual(resp.status_code, 400)  # 401

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
            self.assertEqual(resp.status_code, 200, resp)
            _emails = data['emails'].split('\n')[-1:]
            _users = data['emails'].split('\n')[:-1]
            self.assertEqual(
                set([u.email for u in nc.get_users()]),
                set(_users))
            self.assertEqual(
                set([email for email in nc.get_emails()]),
                set(_emails))

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
        self.assertTrue(len(nc.get_emails()) > 0)
        self.assertTrue(len(nc.get_users()) > 0)
        self.assertEqual(nc.last_send, None)
        self.assertTrue(nc.can_send)
        self.assertEqual(len(mail.outbox), 0)

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
        self.assertEqual(nresp.status_code, 200)
        ndata = json.loads(nresp.content)
        self.assertEqual(set([n['id'] for n in ndata['data']]),
                         set(NotificationCheck.objects.all().values_list('id', flat=True)))
        self.assertTrue(isinstance(nc.last_send, datetime))
        self.assertFalse(nc.can_send)
        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)
        capi.emit_notifications(start)
        self.assertEqual(len(mail.outbox), 0)
        nc.last_send = start - nc.grace_period
        nc.save()
        self.assertTrue(nc.can_send)
        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)
        capi.emit_notifications(start)
        self.assertEqual(len(mail.outbox), nc.receivers.all().count())


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

        self.client.login_user(self.u)
        self.assertTrue(get_user(self.client).is_authenticated())
        resp = self.client.post(autoconf_url)
        self.assertEqual(resp.status_code, 200, resp)


@override_settings(USE_TZ=True)
class MonitoringAnalyticsTestCase(MonitoringTestBase):

    # fixtures = ['metric_data']

    def setUp(self):
        super(MonitoringAnalyticsTestCase, self).setUp()

        call_command('loaddata', 'metric_data', verbosity=0)

        self.username = 'admin'
        self.passwd = 'admin'
        self.admin, _ = get_user_model().objects.get_or_create(username=self.username)
        self.admin.set_password(self.passwd)
        self.admin.is_active = True
        self.admin.is_superuser = True
        self.admin.email = 'test_admin@email.com'
        self.admin.save()

        self._username = 'user'
        self._passwd = 'user'
        self.user, _ = get_user_model().objects.get_or_create(username=self._username)
        self.user.set_password(self._passwd)
        self.user.is_active = True
        self.user.email = 'test_user@email.com'
        self.user.save()

    def test_layer_view_endpoints(self):
        # layer/view
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=view',
            'resource_type=layer'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            self.assertFalse(d["data"])
        last_month_data = data[-1]["data"]
        # First
        self.assertEqual(last_month_data[0]["samples_count"], 2)
        self.assertEqual(last_month_data[0]["val"], "2.0000")
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "2.0000")
        self.assertEqual(
            last_month_data[0]["label"],
            "d2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10"
        )
        self.assertEqual(last_month_data[0]["user"], "joe")
        self.assertEqual(last_month_data[0]["metric_count"], 2)
        # Second
        self.assertEqual(last_month_data[1]["samples_count"], 1)
        self.assertEqual(last_month_data[1]["val"], "1.0000")
        self.assertEqual(last_month_data[1]["min"], "1.0000")
        self.assertEqual(last_month_data[1]["max"], "1.0000")
        self.assertEqual(last_month_data[1]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[1]["label"],
            "68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b"
        )
        self.assertEqual(last_month_data[1]["user"], "mary")
        self.assertEqual(last_month_data[1]["metric_count"], 1)

    def test_layer_upload_endpoints(self):
        # layer/upload
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=upload',
            'resource_type=layer'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            self.assertFalse(d["data"])
        last_month_data = data[-1]["data"]
        # First
        self.assertEqual(last_month_data[0]["samples_count"], 2)
        self.assertEqual(last_month_data[0]["val"], "2.0000")
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "2.0000")
        self.assertEqual(
            last_month_data[0]["label"],
            "d2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10"
        )
        self.assertEqual(last_month_data[0]["user"], "joe")
        self.assertEqual(last_month_data[0]["metric_count"], 2)
        # Second
        self.assertEqual(last_month_data[1]["samples_count"], 1)
        self.assertEqual(last_month_data[1]["val"], "1.0000")
        self.assertEqual(last_month_data[1]["min"], "1.0000")
        self.assertEqual(last_month_data[1]["max"], "1.0000")
        self.assertEqual(last_month_data[1]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[1]["label"],
            "68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b"
        )
        self.assertEqual(last_month_data[1]["user"], "mary")
        self.assertEqual(last_month_data[1]["metric_count"], 1)

    def test_layer_view_metadata_endpoints(self):
        # layer/view_metadata
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=view_metadata',
            'resource_type=layer'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            self.assertFalse(d["data"])
        last_month_data = data[-1]["data"]
        # First
        self.assertEqual(last_month_data[0]["samples_count"], 1)
        self.assertEqual(last_month_data[0]["val"], "1.0000")
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[0]["label"],
            "68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b"
        )
        self.assertEqual(last_month_data[0]["user"], "mary")
        self.assertEqual(last_month_data[0]["metric_count"], 1)
        # Second
        self.assertEqual(last_month_data[1]["samples_count"], 1)
        self.assertEqual(last_month_data[1]["val"], "1.0000")
        self.assertEqual(last_month_data[1]["min"], "1.0000")
        self.assertEqual(last_month_data[1]["max"], "1.0000")
        self.assertEqual(last_month_data[1]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[1]["label"],
            "d2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10"
        )
        self.assertEqual(last_month_data[1]["user"], "joe")
        self.assertEqual(last_month_data[1]["metric_count"], 1)

    def test_layer_change_metadata_endpoints(self):
        # layer/change_metadata
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=change_metadata',
            'resource_type=layer'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            self.assertFalse(d["data"])
        last_month_data = data[-1]["data"]
        # First
        self.assertEqual(last_month_data[0]["samples_count"], 1)
        self.assertEqual(last_month_data[0]["val"], "1.0000")
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[0]["label"],
            "68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b"
        )
        self.assertEqual(last_month_data[0]["user"], "mary")
        self.assertEqual(last_month_data[0]["metric_count"], 1)

    def test_layer_download_endpoints(self):
        # layer/download
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=download',
            'resource_type=layer'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            self.assertFalse(d["data"])
        last_month_data = data[-1]["data"]
        # First
        self.assertEqual(last_month_data[0]["samples_count"], 1)
        self.assertEqual(last_month_data[0]["val"], "1.0000")
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[0]["label"],
            "d2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10"
        )
        self.assertEqual(last_month_data[0]["user"], "joe")
        self.assertEqual(last_month_data[0]["metric_count"], 1)

    def test_map_create_endpoints(self):
        # map/create
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=create',
            'resource_type=map'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            self.assertFalse(d["data"])
        last_month_data = data[-1]["data"]
        # First
        self.assertEqual(last_month_data[0]["samples_count"], 1)
        self.assertEqual(last_month_data[0]["val"], "1.0000")
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[0]["label"],
            "c8f5e7537002284ef547abbb376ca766ec0dff798a7e9f3d428c10af462d146c"
        )
        self.assertEqual(last_month_data[0]["user"], "jhon")
        self.assertEqual(last_month_data[0]["metric_count"], 1)
        # Second
        self.assertEqual(last_month_data[1]["samples_count"], 1)
        self.assertEqual(last_month_data[1]["val"], "1.0000")
        self.assertEqual(last_month_data[1]["min"], "1.0000")
        self.assertEqual(last_month_data[1]["max"], "1.0000")
        self.assertEqual(last_month_data[1]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[1]["label"],
            "d2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10"
        )
        self.assertEqual(last_month_data[1]["user"], "joe")
        self.assertEqual(last_month_data[1]["metric_count"], 1)

    def test_map_change_endpoints(self):
        # map/change
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=change',
            'resource_type=map'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_upload_endpoints(self):
        # document/upload
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=upload',
            'resource_type=document'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_view_metadata_endpoints(self):
        # document/view_metadata
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=view_metadata',
            'resource_type=document'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_change_metadata_endpoints(self):
        # document/change_metadata
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=change_metadata',
            'resource_type=document'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")

        self.client.login_user(self.user)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")

        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_download_endpoints(self):
        # document/download
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=download',
            'resource_type=document'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_url_view_endpoints(self):
        # url/view
        url = "%s?%s&%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'event_type=view',
            'resource_type=url'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            self.assertFalse(d["data"])
        last_month_data = data[-1]["data"]
        # 1
        self.assertEqual(last_month_data[0]["samples_count"], 2)
        self.assertEqual(last_month_data[0]["val"], "2.0000")
        self.assertEqual(last_month_data[0]["min"], "2.0000")
        self.assertEqual(last_month_data[0]["max"], "2.0000")
        self.assertEqual(last_month_data[0]["sum"], "2.0000")
        self.assertEqual(
            last_month_data[0]["label"],
            "3fb62200068b35db416d20bf3e1ef4a1723b3671302c67f7bb36880bfd7dd8a2"
        )
        self.assertEqual(last_month_data[0]["user"], "joe")
        self.assertEqual(last_month_data[0]["metric_count"], 1)
        # 2
        self.assertEqual(last_month_data[1]["samples_count"], 2)
        self.assertEqual(last_month_data[1]["val"], "2.0000")
        self.assertEqual(last_month_data[1]["min"], "1.0000")
        self.assertEqual(last_month_data[1]["max"], "1.0000")
        self.assertEqual(last_month_data[1]["sum"], "2.0000")
        self.assertEqual(
            last_month_data[1]["label"],
            "cf4fca4c598c55ebb2b277378647ef0f961a8d6a28f77f68d2400925821533ac"
        )
        self.assertEqual(last_month_data[1]["user"], "admin")
        self.assertEqual(last_month_data[1]["metric_count"], 2)
        # 3
        self.assertEqual(last_month_data[2]["samples_count"], 2)
        self.assertEqual(last_month_data[2]["val"], "2.0000")
        self.assertEqual(last_month_data[2]["min"], "1.0000")
        self.assertEqual(last_month_data[2]["max"], "1.0000")
        self.assertEqual(last_month_data[2]["sum"], "2.0000")
        self.assertEqual(
            last_month_data[2]["label"],
            "f9db79c41b73a2d6fc5f4a974008798e518a4813a3876da5db33ed0265d0e3bc"
        )
        self.assertEqual(last_month_data[2]["user"], "admin")
        self.assertEqual(last_month_data[2]["metric_count"], 2)
        # 4
        self.assertEqual(last_month_data[3]["samples_count"], 1)
        self.assertEqual(last_month_data[3]["val"], "1.0000")
        self.assertEqual(last_month_data[3]["min"], "1.0000")
        self.assertEqual(last_month_data[3]["max"], "1.0000")
        self.assertEqual(last_month_data[3]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[3]["label"],
            "8cfca7c4dbb8b54164c9f62e53e639f6e6db2814f299b9c202dc1b8c3797b773"
        )
        self.assertEqual(last_month_data[3]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[3]["metric_count"], 1)
        # 5
        self.assertEqual(last_month_data[4]["samples_count"], 1)
        self.assertEqual(last_month_data[4]["val"], "1.0000")
        self.assertEqual(last_month_data[4]["min"], "1.0000")
        self.assertEqual(last_month_data[4]["max"], "1.0000")
        self.assertEqual(last_month_data[4]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[4]["label"],
            "9d013cdaef339aedf8794f6558aacf4eaf5eddfaee11b6316b05105ea5b1968a"
        )
        self.assertEqual(last_month_data[4]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[4]["metric_count"], 1)
        # 6
        self.assertEqual(last_month_data[5]["samples_count"], 1)
        self.assertEqual(last_month_data[5]["val"], "1.0000")
        self.assertEqual(last_month_data[5]["min"], "1.0000")
        self.assertEqual(last_month_data[5]["max"], "1.0000")
        self.assertEqual(last_month_data[5]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[5]["label"],
            "bc1b2cea3df6bd09c27ae5b8f81a645f83a8dfb0ff83b9efb78a6be6a9ffa99e"
        )
        self.assertEqual(last_month_data[5]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[5]["metric_count"], 1)
        # 7
        self.assertEqual(last_month_data[6]["samples_count"], 1)
        self.assertEqual(last_month_data[6]["val"], "1.0000")
        self.assertEqual(last_month_data[6]["min"], "1.0000")
        self.assertEqual(last_month_data[6]["max"], "1.0000")
        self.assertEqual(last_month_data[6]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[6]["label"],
            "2365500a901139d13d9271b17a0d2bf42efb228aa7afef29aaee4179d5f6be3b"
        )
        self.assertEqual(last_month_data[6]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[6]["metric_count"], 1)
        # 8
        self.assertEqual(last_month_data[7]["samples_count"], 1)
        self.assertEqual(last_month_data[7]["val"], "1.0000")
        self.assertEqual(last_month_data[7]["min"], "1.0000")
        self.assertEqual(last_month_data[7]["max"], "1.0000")
        self.assertEqual(last_month_data[7]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[7]["label"],
            "c8f5e7537002284ef547abbb376ca766ec0dff798a7e9f3d428c10af462d146c"
        )
        self.assertEqual(last_month_data[7]["user"], "jhon")
        self.assertEqual(last_month_data[7]["metric_count"], 1)
        # 9
        self.assertEqual(last_month_data[8]["samples_count"], 1)
        self.assertEqual(last_month_data[8]["val"], "1.0000")
        self.assertEqual(last_month_data[8]["min"], "1.0000")
        self.assertEqual(last_month_data[8]["max"], "1.0000")
        self.assertEqual(last_month_data[8]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[8]["label"],
            "ce5e2908916d029e9ba3c1e3dd27ea568d356f6a0ed05c7309a834260d51e996"
        )
        self.assertEqual(last_month_data[8]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[8]["metric_count"], 1)
        # 10
        self.assertEqual(last_month_data[9]["samples_count"], 1)
        self.assertEqual(last_month_data[9]["val"], "1.0000")
        self.assertEqual(last_month_data[9]["min"], "1.0000")
        self.assertEqual(last_month_data[9]["max"], "1.0000")
        self.assertEqual(last_month_data[9]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[9]["label"],
            "d2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10"
        )
        self.assertEqual(last_month_data[9]["user"], "joe")
        self.assertEqual(last_month_data[9]["metric_count"], 1)
        # 11
        self.assertEqual(last_month_data[10]["samples_count"], 1)
        self.assertEqual(last_month_data[10]["val"], "1.0000")
        self.assertEqual(last_month_data[10]["min"], "1.0000")
        self.assertEqual(last_month_data[10]["max"], "1.0000")
        self.assertEqual(last_month_data[10]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[10]["label"],
            "f35fc9dd6dd617d3c9cc6f984ff9e421ce6e83420b049d9a68f9c62bcbaa4322"
        )
        self.assertEqual(last_month_data[10]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[10]["metric_count"], 1)
        # 12
        self.assertEqual(last_month_data[11]["samples_count"], 1)
        self.assertEqual(last_month_data[11]["val"], "1.0000")
        self.assertEqual(last_month_data[11]["min"], "1.0000")
        self.assertEqual(last_month_data[11]["max"], "1.0000")
        self.assertEqual(last_month_data[11]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[11]["label"],
            "bed96eb3d8b4905d47b59774121200232042b9b2745bc9eb819ab61c83a20379"
        )
        self.assertEqual(last_month_data[11]["user"], "admin")
        self.assertEqual(last_month_data[11]["metric_count"], 1)
        # 13
        self.assertEqual(last_month_data[12]["samples_count"], 1)
        self.assertEqual(last_month_data[12]["val"], "1.0000")
        self.assertEqual(last_month_data[12]["min"], "1.0000")
        self.assertEqual(last_month_data[12]["max"], "1.0000")
        self.assertEqual(last_month_data[12]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[12]["label"],
            "68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b"
        )
        self.assertEqual(last_month_data[12]["user"], "mary")
        self.assertEqual(last_month_data[12]["metric_count"], 1)
        # 14
        self.assertEqual(last_month_data[13]["samples_count"], 1)
        self.assertEqual(last_month_data[13]["val"], "1.0000")
        self.assertEqual(last_month_data[13]["min"], "1.0000")
        self.assertEqual(last_month_data[13]["max"], "1.0000")
        self.assertEqual(last_month_data[13]["sum"], "1.0000")
        self.assertEqual(
            last_month_data[13]["label"],
            "7447fc6af5d3c693fb6250f0db31e5a9c2de10e37607be6ff015c89172522ebb"
        )
        self.assertEqual(last_month_data[13]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[13]["metric_count"], 1)

    def test_resources_endpoint(self):
        url = reverse('monitoring:api_resources')
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "resources")
        resources = out["resources"]
        self.assertEqual(len(resources), 6)
        for i, r in enumerate(resources):
            if resources[i]["name"] == "San Francisco Transport Map":
                # San Francisco Transport Map
                self.assertEqual(resources[i]["type"], "map")
            elif resources[i]["name"] == "geonode:waterways":
                # geonode:waterways
                self.assertEqual(resources[i]["type"], "layer")
            elif resources[i]["name"] == "geonode:railways":
                # geonode:railways
                self.assertEqual(resources[i]["type"], "layer")
            elif resources[i]["name"] == "Amsterdam Waterways Map":
                # Amsterdam Waterways Map
                self.assertEqual(resources[i]["type"], "map")
            elif resources[i]["name"] == "geonode:roads":
                # geonode:roads
                self.assertEqual(resources[i]["type"], "layer")
            elif resources[i]["name"] == "/":
                # home
                self.assertEqual(resources[i]["type"], "url")

    def test_resource_types_endpoint(self):
        url = reverse('monitoring:api_resource_types')
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "resource_types")
        resources = out["resource_types"]
        # No resource
        self.assertEqual(resources[0]["type_label"], "No resource")
        self.assertEqual(resources[0]["name"], "")
        # Layer
        self.assertEqual(resources[1]["type_label"], "Layer")
        self.assertEqual(resources[1]["name"], "layer")
        # Map
        self.assertEqual(resources[2]["type_label"], "Map")
        self.assertEqual(resources[2]["name"], "map")
        # Resource Base
        self.assertEqual(resources[3]["type_label"], "Resource base")
        self.assertEqual(resources[3]["name"], "resource_base")
        # Document
        self.assertEqual(resources[4]["type_label"], "Document")
        self.assertEqual(resources[4]["name"], "document")
        # Style
        self.assertEqual(resources[5]["type_label"], "Style")
        self.assertEqual(resources[5]["name"], "style")
        # Admin
        self.assertEqual(resources[6]["type_label"], "Admin")
        self.assertEqual(resources[6]["name"], "admin")
        # url
        self.assertEqual(resources[7]["type_label"], "URL")
        self.assertEqual(resources[7]["name"], "url")
        # other
        self.assertEqual(resources[8]["type_label"], "Other")
        self.assertEqual(resources[8]["name"], "other")

    def test_event_types_endpoint(self):
        url = reverse('monitoring:api_event_types')
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "event_types")
        resources = out["event_types"]
        # OWS:TMS
        self.assertEqual(resources[0]["type_label"], "TMS")
        self.assertEqual(resources[0]["name"], "OWS:TMS")
        # OWS:WMS-C
        self.assertEqual(resources[1]["type_label"], "WMS-C")
        self.assertEqual(resources[1]["name"], "OWS:WMS-C")
        # OWS:WMTS
        self.assertEqual(resources[2]["type_label"], "WMTS")
        self.assertEqual(resources[2]["name"], "OWS:WMTS")
        # OWS:WCS
        self.assertEqual(resources[3]["type_label"], "WCS")
        self.assertEqual(resources[3]["name"], "OWS:WCS")
        # OWS:WFS
        self.assertEqual(resources[4]["type_label"], "WFS")
        self.assertEqual(resources[4]["name"], "OWS:WFS")
        # OWS:WMS
        self.assertEqual(resources[5]["type_label"], "WMS")
        self.assertEqual(resources[5]["name"], "OWS:WMS")
        # OWS:WPS
        self.assertEqual(resources[6]["type_label"], "WPS")
        self.assertEqual(resources[6]["name"], "OWS:WPS")
        # other
        self.assertEqual(resources[7]["type_label"], "Not OWS")
        self.assertEqual(resources[7]["name"], "other")
        # OWS:ALL
        self.assertEqual(resources[8]["type_label"], "Any OWS")
        self.assertEqual(resources[8]["name"], "OWS:ALL")
        # all
        self.assertEqual(resources[9]["type_label"], "All")
        self.assertEqual(resources[9]["name"], "all")
        # create
        self.assertEqual(resources[10]["type_label"], "Create")
        self.assertEqual(resources[10]["name"], "create")
        # upload
        self.assertEqual(resources[11]["type_label"], "Upload")
        self.assertEqual(resources[11]["name"], "upload")
        # other
        self.assertEqual(resources[12]["type_label"], "Change")
        self.assertEqual(resources[12]["name"], "change")
        # change_metadata
        self.assertEqual(resources[13]["type_label"], "Change Metadata")
        self.assertEqual(resources[13]["name"], "change_metadata")
        # view_metadata
        self.assertEqual(resources[14]["type_label"], "View Metadata")
        self.assertEqual(resources[14]["name"], "view_metadata")
        # view
        self.assertEqual(resources[15]["type_label"], "View")
        self.assertEqual(resources[15]["name"], "view")
        # download
        self.assertEqual(resources[16]["type_label"], "Download")
        self.assertEqual(resources[16]["name"], "download")
        # publish
        self.assertEqual(resources[17]["type_label"], "Publish")
        self.assertEqual(resources[17]["name"], "publish")
        # remove
        self.assertEqual(resources[18]["type_label"], "Remove")
        self.assertEqual(resources[18]["name"], "remove")
        # geoserver
        self.assertEqual(resources[19]["type_label"], "Geoserver event")
        self.assertEqual(resources[19]["name"], "geoserver")

    def test_unique_visitors_count_endpoints(self):
        # layer/upload
        url = "%s?%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'group_by=user'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            month_data = d["data"]
            self.assertEqual(len(month_data), 1)
            self.assertEqual(month_data[0]["metric_count"], 0)
            self.assertEqual(month_data[0]["val"], 0)
            self.assertEqual(month_data[0]["min"], None)
            self.assertEqual(month_data[0]["max"], None)
            self.assertEqual(month_data[0]["sum"], None)
            self.assertEqual(month_data[0]["samples_count"], None)
        last_month_data = data[-1]["data"]
        self.assertEqual(len(last_month_data), 1)
        self.assertEqual(last_month_data[0]["metric_count"], 26)
        self.assertEqual(last_month_data[0]["val"], 5)
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "3.0000")
        self.assertEqual(last_month_data[0]["sum"], "32.0000")
        self.assertEqual(last_month_data[0]["samples_count"], 32)

    def test_anonymous_sessions_count_endpoints(self):
        # layer/upload
        url = "%s?%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'group_by=label&user=AnonymousUser'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            month_data = d["data"]
            self.assertEqual(len(month_data), 1)
            self.assertEqual(month_data[0]["metric_count"], 0)
            self.assertEqual(month_data[0]["val"], 0)
            self.assertEqual(month_data[0]["min"], None)
            self.assertEqual(month_data[0]["max"], None)
            self.assertEqual(month_data[0]["sum"], None)
            self.assertEqual(month_data[0]["samples_count"], None)
        last_month_data = data[-1]["data"]
        self.assertEqual(len(last_month_data), 1)
        self.assertEqual(last_month_data[0]["metric_count"], 7)
        self.assertEqual(last_month_data[0]["val"], 7)
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "7.0000")
        self.assertEqual(last_month_data[0]["samples_count"], 7)

    def test_unique_visitors_list_endpoints(self):
        # layer/upload
        url = "%s?%s&%s" % (
            reverse('monitoring:api_metric_data', args={'request.users'}),
            'valid_from=2018-08-29T20:00:00.000Z&valid_to=2019-08-29T20:00:00.000Z&interval=2628000',
            'group_by=user_on_label'
        )
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(response.content)
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated())
        response = self.client.get(url)
        out = json.loads(response.content)
        data = out["data"]["data"]
        metric = out["data"]["metric"]
        interval = out["data"]["interval"]
        label = out["data"]["label"]
        valid_from = out["data"]["input_valid_from"]
        valid_to = out["data"]["input_valid_to"]
        axis_label = out["data"]["axis_label"]
        type = out["data"]["type"]
        self.assertEqual(metric, 'request.users')
        self.assertEqual(interval, 2628000)
        self.assertEqual(label, None)
        self.assertEqual(valid_from, '2018-08-29T20:00:00Z')
        self.assertEqual(valid_to, '2019-08-29T20:00:00Z')
        self.assertEqual(axis_label, 'Count')
        self.assertEqual(type, 'value')
        # check data
        self.assertEqual(len(data), 12)  # 12 months
        for d in data[:-1]:
            month_data = d["data"]
            self.assertEqual(len(month_data), 0)
        last_month_data = data[-1]["data"]
        self.assertEqual(len(last_month_data), 5)
        # 1
        self.assertEqual(last_month_data[0]["metric_count"], 7)
        self.assertEqual(last_month_data[0]["val"], 7)
        self.assertEqual(last_month_data[0]["min"], "1.0000")
        self.assertEqual(last_month_data[0]["max"], "1.0000")
        self.assertEqual(last_month_data[0]["sum"], "7.0000")
        self.assertEqual(last_month_data[0]["user"], "AnonymousUser")
        self.assertEqual(last_month_data[0]["samples_count"], 7)
        # 2
        self.assertEqual(last_month_data[1]["metric_count"], 5)
        self.assertEqual(last_month_data[1]["val"], 3)
        self.assertEqual(last_month_data[1]["min"], "1.0000")
        self.assertEqual(last_month_data[1]["max"], "1.0000")
        self.assertEqual(last_month_data[1]["sum"], "5.0000")
        self.assertEqual(last_month_data[1]["user"], "admin")
        self.assertEqual(last_month_data[1]["samples_count"], 5)
        # 3
        self.assertEqual(last_month_data[2]["metric_count"], 8)
        self.assertEqual(last_month_data[2]["val"], 2)
        self.assertEqual(last_month_data[2]["min"], "1.0000")
        self.assertEqual(last_month_data[2]["max"], "3.0000")
        self.assertEqual(last_month_data[2]["sum"], "12.0000")
        self.assertEqual(last_month_data[2]["user"], "joe")
        self.assertEqual(last_month_data[2]["samples_count"], 12)
        # 4
        self.assertEqual(last_month_data[3]["metric_count"], 3)
        self.assertEqual(last_month_data[3]["val"], 1)
        self.assertEqual(last_month_data[3]["min"], "1.0000")
        self.assertEqual(last_month_data[3]["max"], "1.0000")
        self.assertEqual(last_month_data[3]["sum"], "3.0000")
        self.assertEqual(last_month_data[3]["user"], "jhon")
        self.assertEqual(last_month_data[3]["samples_count"], 3)
        # 5
        self.assertEqual(last_month_data[4]["metric_count"], 3)
        self.assertEqual(last_month_data[4]["val"], 1)
        self.assertEqual(last_month_data[4]["min"], "1.0000")
        self.assertEqual(last_month_data[4]["max"], "2.0000")
        self.assertEqual(last_month_data[4]["sum"], "5.0000")
        self.assertEqual(last_month_data[4]["user"], "mary")
        self.assertEqual(last_month_data[4]["samples_count"], 5)
