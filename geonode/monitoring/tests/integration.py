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

from geonode.tests.base import GeoNodeLiveTestSupport

from datetime import datetime, timedelta

import os
import time
import json
import pytz
import logging
import os.path
import xmljson
import dj_database_url

from decimal import Decimal  # noqa
from importlib import import_module
from defusedxml import lxml as dlxml

from django.core import mail
from django.conf import settings
from django.db import connections
from django.urls import reverse
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
from geonode.compat import ensure_string
from geonode.monitoring.collector import CollectorAPI
from geonode.monitoring.utils import generate_periods, align_period_start
from geonode.base.models import ResourceBase
from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.documents.models import Document
from geonode.monitoring.models import *  # noqa

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

DB_HOST = settings.DATABASES['default']['HOST']
DB_PORT = settings.DATABASES['default']['PORT']
DB_NAME = settings.DATABASES['default']['NAME']
DB_USER = settings.DATABASES['default']['USER']
DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
DATASTORE_URL = f'postgis://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
postgis_db = dj_database_url.parse(DATASTORE_URL, conn_max_age=0)

logging.getLogger('south').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# create test user if needed, delete all layers and set password
u, created = get_user_model().objects.get_or_create(username=GEONODE_USER)
if created:
    u.set_password(GEONODE_PASSWD)
    u.save()
else:
    Layer.objects.filter(owner=u).delete()

res_dir = os.path.join(os.path.dirname(__file__), 'resources')
req_err_path = os.path.join(res_dir, 'req_err.xml')
req_path = os.path.join(res_dir, 'req.xml')

with open(req_err_path) as req_err_xml_file:
    req_err_xml = req_err_xml_file.read()
with open(req_path) as req_xml_file:
    req_xml = req_xml_file.read()

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
                f'{morsel.key}={morsel.coded_value}'
                for morsel in self.cookies.values()
            )),
            'PATH_INFO': '/',
            'REMOTE_ADDR': '127.0.0.1',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': '80',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
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
        user.backend = f"{'django.contrib.auth.backends'}.{'ModelBackend'}"

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
        ResourceBase.objects.all().update(dirty_state=False)
        # await startup
        cl = Client(
            GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        )
        for i in range(10):
            time.sleep(.2)
            try:
                cl.get_html('/', debug=False)
                break
            except Exception:
                pass

        self.catalog = Catalog(
            f"{GEOSERVER_URL}rest",
            GEOSERVER_USER,
            GEOSERVER_PASSWD,
            retries=ogc_server_settings.MAX_RETRIES,
            backoff_factor=ogc_server_settings.BACKOFF_FACTOR
        )

        self.client = TestClient(REMOTE_ADDR='127.0.0.1')

        settings.DATABASES['default']['NAME'] = DB_NAME
        settings.OGC_SERVER['default']['DATASTORE'] = ''

        connections['default'].settings_dict['ATOMIC_REQUESTS'] = False
        connections['default'].connect()

        self._tempfiles = []

    def _post_teardown(self):
        pass

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

        for temp_file in self._tempfiles:
            os.unlink(temp_file)

        # Cleanup
        Layer.objects.all().delete()
        Map.objects.all().delete()
        Document.objects.all().delete()

        MetricValue.objects.all().delete()
        ExceptionEvent.objects.all().delete()
        RequestEvent.objects.all().delete()
        MonitoredResource.objects.all().delete()
        try:
            NotificationCheck.objects.all().delete()
        except Exception:
            pass
        Service.objects.all().delete()
        Host.objects.all().delete()

        from django.conf import settings
        if settings.OGC_SERVER['default'].get(
                "GEOFENCE_SECURITY_ENABLED", False):
            from geonode.security.utils import purge_geofence_all
            purge_geofence_all()


@override_settings(USE_TZ=True)
class RequestsTestCase(MonitoringTestBase):

    def setUp(self):
        super().setUp()

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
        self.assertTrue(get_user(self.client).is_authenticated)

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

        if RequestEvent.objects.all().count():
            rq = RequestEvent.objects.all().last()
            self.assertTrue(rq.response_time > 0)
            self.assertEqual(
                list(rq.resources.values_list('name', 'type')), [(_l.alternate, 'layer',)])
            self.assertEqual(rq.request_method, 'GET')

    def test_gn_error(self):
        """
        Test if we get geonode errors logged
        """
        self.client.login_user(self.u)
        self.assertTrue(get_user(self.client).is_authenticated)

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
        eq = ExceptionEvent.objects.all().last()
        if eq:
            self.assertEqual('django.http.response.Http404', eq.error_type)

    def test_service_handlers(self):
        """
        Test if we can calculate metrics
        """
        self.client.login_user(self.u)
        self.assertTrue(get_user(self.client).is_authenticated)

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
        if requests:
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

    def test_collect_metrics_command(self):
        """
        Test that collect metrics command is executed sequentially
        """
        self.client.login_user(self.u)
        self.assertTrue(get_user(self.client).is_authenticated)

        from geonode.monitoring.tasks import collect_metrics
        execution_times = []
        for _r in range(10):
            result = collect_metrics.apply_async()
            exec_tuple = result.get()
            if exec_tuple:
                execution_times.append(exec_tuple[0])
                execution_times.append(exec_tuple[1])

        for _r in range(len(execution_times) - 1):
            self.assertTrue(execution_times[_r] < execution_times[_r + 1])


@override_settings(USE_TZ=True)
class MonitoringUtilsTestCase(MonitoringTestBase):

    def setUp(self):
        super().setUp()

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
        super().setUp()

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
        mc, _ = MetricNotificationCheck.objects.get_or_create(notification_check=nc,
                                                              service=self.service,
                                                              metric=self.metric,
                                                              min_value=None,
                                                              definition=nc.definitions.first(),
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
        nc, _ = NotificationCheck.objects.get_or_create(
            name='check requests',
            description='check requests')

        MetricNotificationCheck.objects.get_or_create(notification_check=nc,
                                                      service=self.service,
                                                      metric=self.metric,
                                                      min_value=10,
                                                      max_value=200,
                                                      resource=resource,
                                                      max_timeout=None)

        self.client.login_user(self.u)
        self.assertTrue(get_user(self.client).is_authenticated)

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(ensure_string(nresp.content))
        self.assertTrue(data['data'][0]['id'])

        nresp = self.client.get(
            reverse('monitoring:api_user_notification_config',
                    kwargs={'pk': nc.id}))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(ensure_string(nresp.content))
        self.assertTrue(data['data']['notification']['id'])

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(ensure_string(nresp.content))
        self.assertTrue(data['data'][0]['id'])

        self.client.login_user(self.u2)
        self.assertTrue(get_user(self.client).is_authenticated)

        nresp = self.client.get(reverse('monitoring:api_user_notifications'))
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200, nresp)
        data = json.loads(ensure_string(nresp.content))
        self.assertTrue(len(data['data']) > 0)

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
        self.assertTrue(get_user(self.client).is_authenticated)
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
        self.assertIsNotNone(out)

        if out.status_code == 200:
            jout = json.loads(ensure_string(out.content))
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

        if out.status_code == 200:
            jout = json.loads(ensure_string(out.content))
            notifications = NotificationCheck.objects.all()
            for n in notifications:
                if n.is_error:
                    self.assertTrue(MetricNotificationCheck.objects.all().exists())
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

        if out.status_code == 200:
            jout = json.loads(ensure_string(out.content))
            notifications = NotificationCheck.objects.all()
            for n in notifications:
                if n.is_error:
                    self.assertTrue(MetricNotificationCheck.objects.all().exists())
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
        self.assertTrue(get_user(self.client).is_authenticated)
        for nc in NotificationCheck.objects.all():
            notifications_config_url = reverse(
                'monitoring:api_user_notification_config', args=(nc.id,))
            nc_form = nc.get_user_form()
            self.assertTrue(nc_form)
            self.assertTrue(len(nc_form.fields.keys()) > 0)
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
            if resp.status_code == 200:
                _emails = data['emails'].split('\n')[-1:]
                _users = data['emails'].split('\n')[:-1]
                self.assertEqual(
                    {u.email for u in nc.get_users()},
                    set(_users))
                self.assertEqual(
                    {email for email in nc.get_emails()},
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

        nc = NotificationCheck.objects.all().last()
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

        nc.refresh_from_db()
        notifications_url = reverse('monitoring:api_user_notifications')
        nresp = self.client.get(notifications_url)
        self.assertIsNotNone(nresp)
        self.assertEqual(nresp.status_code, 200)
        ndata = json.loads(ensure_string(nresp.content))
        self.assertEqual({n['id'] for n in ndata['data']},
                         set(NotificationCheck.objects.values_list('id', flat=True)))
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
        super().setUp()

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
        self.assertTrue(get_user(self.client).is_authenticated)
        resp = self.client.post(autoconf_url)
        self.assertEqual(resp.status_code, 200, resp)


@override_settings(USE_TZ=True)
class MonitoringAnalyticsTestCase(MonitoringTestBase):

    # fixtures = ['metric_data']

    def setUp(self):
        super().setUp()

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
        layer_view_data = [
            {'label': 'd2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10',
             'max': '1.0000',
             'metric_count': 2,
             'min': '1.0000',
             'samples_count': 2,
             'sum': '2.0000',
             'user': 'joe',
             'val': '2.0000'},
            {'label': '68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'mary',
             'val': '1.0000'}
        ]
        # layer/view
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=view'}&{'resource_type=layer'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(layer_view_data))
                for dd in month_data:
                    self.assertIn(dd, layer_view_data)
        self.assertEqual(empty_months, 11)

    def test_layer_upload_endpoints(self):
        layer_upload_data = [
            {'label': 'd2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10',
             'max': '1.0000',
             'metric_count': 2,
             'min': '1.0000',
             'samples_count': 2,
             'sum': '2.0000',
             'user': 'joe',
             'val': '2.0000'},
            {'label': '68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'mary',
             'val': '1.0000'}
        ]
        # layer/upload
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=upload'}&{'resource_type=layer'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(layer_upload_data))
                for dd in month_data:
                    self.assertIn(dd, layer_upload_data)
        self.assertEqual(empty_months, 11)

    def test_layer_view_metadata_endpoints(self):
        layer_view_metadata_data = [
            {'label': '68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'mary',
             'val': '1.0000'},
            {'label': 'd2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'joe',
             'val': '1.0000'}
        ]
        # layer/view_metadata
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=view_metadata'}&{'resource_type=layer'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(layer_view_metadata_data))
                for dd in month_data:
                    self.assertIn(dd, layer_view_metadata_data)
        self.assertEqual(empty_months, 11)

    def test_layer_change_metadata_endpoints(self):
        layer_change_data = [
            {'label': '68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'mary',
             'val': '1.0000'}
        ]
        # layer/change_metadata
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=change_metadata'}&{'resource_type=layer'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(layer_change_data))
                for dd in month_data:
                    self.assertIn(dd, layer_change_data)
        self.assertEqual(empty_months, 11)

    def test_layer_download_endpoints(self):
        layer_downloads_data = [
            {'label': 'd2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'joe',
             'val': '1.0000'}
        ]
        # layer/download
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=download'}&{'resource_type=layer'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(layer_downloads_data))
                for dd in month_data:
                    self.assertIn(dd, layer_downloads_data)
        self.assertEqual(empty_months, 11)

    def test_map_create_endpoints(self):
        map_creation_data = [
            {'label': 'c8f5e7537002284ef547abbb376ca766ec0dff798a7e9f3d428c10af462d146c',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'jhon',
             'val': '1.0000'},
            {'label': 'd2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'joe',
             'val': '1.0000'}
        ]
        # map/create
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=create'}&{'resource_type=map'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(map_creation_data))
                for dd in month_data:
                    self.assertIn(dd, map_creation_data)
        self.assertEqual(empty_months, 11)

    def test_map_change_endpoints(self):
        # map/change
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=change'}&{'resource_type=map'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_upload_endpoints(self):
        # document/upload
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=upload'}&{'resource_type=document'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_view_metadata_endpoints(self):
        # document/view_metadata
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=view_metadata'}&{'resource_type=document'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_change_metadata_endpoints(self):
        # document/change_metadata
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=change_metadata'}&{'resource_type=document'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")

        self.client.login_user(self.user)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(d["data"])

    def test_document_download_endpoints(self):
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=download'}&{'resource_type=document'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        for d in data:
            self.assertFalse(len(d["data"]))

    def test_url_view_endpoints(self):
        url_view_data = [
            {'label': '3fb62200068b35db416d20bf3e1ef4a1723b3671302c67f7bb36880bfd7dd8a2',
             'max': '2.0000',
             'metric_count': 1,
             'min': '2.0000',
             'samples_count': 2,
             'sum': '2.0000',
             'user': 'joe',
             'val': '2.0000'},
            {'label': 'cf4fca4c598c55ebb2b277378647ef0f961a8d6a28f77f68d2400925821533ac',
             'max': '1.0000',
             'metric_count': 2,
             'min': '1.0000',
             'samples_count': 2,
             'sum': '2.0000',
             'user': 'admin',
             'val': '2.0000'},
            {'label': 'f9db79c41b73a2d6fc5f4a974008798e518a4813a3876da5db33ed0265d0e3bc',
             'max': '1.0000',
             'metric_count': 2,
             'min': '1.0000',
             'samples_count': 2,
             'sum': '2.0000',
             'user': 'admin',
             'val': '2.0000'},
            {'label': '8cfca7c4dbb8b54164c9f62e53e639f6e6db2814f299b9c202dc1b8c3797b773',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'AnonymousUser',
             'val': '1.0000'},
            {'label': '9d013cdaef339aedf8794f6558aacf4eaf5eddfaee11b6316b05105ea5b1968a',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'AnonymousUser',
             'val': '1.0000'},
            {'label': 'bc1b2cea3df6bd09c27ae5b8f81a645f83a8dfb0ff83b9efb78a6be6a9ffa99e',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'AnonymousUser',
             'val': '1.0000'},
            {'label': '2365500a901139d13d9271b17a0d2bf42efb228aa7afef29aaee4179d5f6be3b',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'AnonymousUser',
             'val': '1.0000'},
            {'label': 'c8f5e7537002284ef547abbb376ca766ec0dff798a7e9f3d428c10af462d146c',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'jhon',
             'val': '1.0000'},
            {'label': 'ce5e2908916d029e9ba3c1e3dd27ea568d356f6a0ed05c7309a834260d51e996',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'AnonymousUser',
             'val': '1.0000'},
            {'label': 'd2e837d24027cfd1ca361d60a63fc4f474993bd909bffbcc83117c3c76653c10',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'joe',
             'val': '1.0000'},
            {'label': 'f35fc9dd6dd617d3c9cc6f984ff9e421ce6e83420b049d9a68f9c62bcbaa4322',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'AnonymousUser',
             'val': '1.0000'},
            {'label': 'bed96eb3d8b4905d47b59774121200232042b9b2745bc9eb819ab61c83a20379',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'admin',
             'val': '1.0000'},
            {'label': '68ce3486a49de17ac675ead5ba963cc31a0444bd7eb7c6da9db17c933637186b',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'mary',
             'val': '1.0000'},
            {'label': '7447fc6af5d3c693fb6250f0db31e5a9c2de10e37607be6ff015c89172522ebb',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'user': 'AnonymousUser',
             'val': '1.0000'}
        ]
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'event_type=view'}&{'resource_type=url'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(url_view_data))
                for dd in month_data:
                    self.assertIn(dd, url_view_data)
        self.assertEqual(empty_months, 11)

    def test_resources_endpoint(self):
        resources_data = [
            {'id': 2, 'name': 'geonode:roads', 'type': 'layer'},
            {'id': 5, 'name': 'geonode:waterways', 'type': 'layer'},
            {'id': 6, 'name': 'Amsterdam Waterways Map', 'type': 'map'},
            {'id': 3, 'name': 'geonode:railways', 'type': 'layer'},
            {'id': 1, 'name': '/', 'type': 'url'},
            {'id': 4, 'name': 'San Francisco Transport Map', 'type': 'map'}
        ]
        url = reverse('monitoring:api_resources')
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "resources")
        resources = out["resources"]
        self.assertEqual(len(resources), len(resources_data))
        for r in resources:
            self.assertIn(r, resources_data)

    def test_resource_types_endpoint(self):
        resource_types = [
            {'name': '', 'type_label': 'No resource'},
            {'name': 'layer', 'type_label': 'Layer'},
            {'name': 'map', 'type_label': 'Map'},
            {'name': 'resource_base', 'type_label': 'Resource base'},
            {'name': 'document', 'type_label': 'Document'},
            {'name': 'style', 'type_label': 'Style'},
            {'name': 'admin', 'type_label': 'Admin'},
            {'name': 'url', 'type_label': 'URL'},
            {'name': 'other', 'type_label': 'Other'}
        ]
        url = reverse('monitoring:api_resource_types')
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "resource_types")
        resources = out["resource_types"]
        self.assertEqual(len(resources), len(resource_types))
        for r in resources:
            self.assertIn(r, resource_types)

    def test_users_count_for_resource_endpoint(self):
        users_count_data = [
            {
                'max': '2.0000',
                'metric_count': 16,
                'min': '1.0000',
                'resource': {
                    'href': '/',
                    'id': 1,
                    'name': '/',
                    'type': 'url'
                },
                'samples_count': 17,
                'sum': '17.0000',
                'val': 5
            },
            {
                'max': '2.0000',
                'metric_count': 3,
                'min': '1.0000',
                'resource': {
                    'href': '',
                    'id': 5,
                    'name': 'geonode:waterways',
                    'type': 'layer'
                },
                'samples_count': 5,
                'sum': '5.0000',
                'val': 2
            },
            {
                'max': '2.0000',
                'metric_count': 2,
                'min': '1.0000',
                'resource': {
                    'href': '',
                    'id': 2,
                    'name': 'geonode:roads',
                    'type': 'layer'
                },
                'samples_count': 3,
                'sum': '3.0000',
                'val': 1
            },
            {
                'max': '3.0000',
                'metric_count': 2,
                'min': '1.0000',
                'resource': {
                    'href': '',
                    'id': 3,
                    'name': 'geonode:railways',
                    'type': 'layer'
                },
                'samples_count': 4,
                'sum': '4.0000',
                'val': 1
            },
            {
                'max': '1.0000',
                'metric_count': 1,
                'min': '1.0000',
                'resource': {
                    'href': '',
                    'id': 4,
                    'name': 'San Francisco Transport Map',
                    'type': 'map'
                },
                'samples_count': 1,
                'sum': '1.0000',
                'val': 1
            },
            {
                'max': '1.0000',
                'metric_count': 1,
                'min': '1.0000',
                'resource': {
                    'href': '',
                    'id': 6,
                    'name': 'Amsterdam Waterways Map',
                    'type': 'map'
                },
                'samples_count': 1,
                'sum': '1.0000',
                'val': 1
            }
        ]
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'group_by=resource_on_user'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 31536000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"][0]["data"]
        self.assertEqual(len(data), len(users_count_data))
        for d in data:
            self.assertIn(d, users_count_data)

    def test_resources_count_endpoint(self):
        resource_count_data = [
            {
                'max': '4.0000',
                'metric_count': 16,
                'min': '1.0000',
                'samples_count': 31,
                'sum': '31.0000',
                'val': 6
            }
        ]
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.count'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'group_by=count_on_resource'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.count')
        self.assertEqual(out["data"]["interval"], 31536000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'count')
        data = out["data"]["data"][0]["data"]
        self.assertEqual(len(data), len(resource_count_data))
        for d in data:
            self.assertIn(d, resource_count_data)

    def test_event_types_endpoint(self):
        event_types_data = [
            {'name': 'OWS:TMS', 'type_label': 'TMS'},
            {'name': 'OWS:WMS-C', 'type_label': 'WMS-C'},
            {'name': 'OWS:WMTS', 'type_label': 'WMTS'},
            {'name': 'OWS:WCS', 'type_label': 'WCS'},
            {'name': 'OWS:WFS', 'type_label': 'WFS'},
            {'name': 'OWS:WMS', 'type_label': 'WMS'},
            {'name': 'OWS:WPS', 'type_label': 'WPS'},
            {'name': 'other', 'type_label': 'Not OWS'},
            {'name': 'OWS:ALL', 'type_label': 'Any OWS'},
            {'name': 'all', 'type_label': 'All'},
            {'name': 'create', 'type_label': 'Create'},
            {'name': 'upload', 'type_label': 'Upload'},
            {'name': 'change', 'type_label': 'Change'},
            {'name': 'change_metadata', 'type_label': 'Change Metadata'},
            {'name': 'view_metadata', 'type_label': 'View Metadata'},
            {'name': 'view', 'type_label': 'View'},
            {'name': 'download', 'type_label': 'Download'},
            {'name': 'publish', 'type_label': 'Publish'},
            {'name': 'remove', 'type_label': 'Remove'},
            {'name': 'geoserver', 'type_label': 'Geoserver event'}
        ]
        url = reverse('monitoring:api_event_types')
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "event_types")
        resources = out["event_types"]
        self.assertEqual(len(resources), len(event_types_data))
        for r in resources:
            self.assertIn(r, event_types_data)

    def test_ows_service_enpoints(self):
        ows_events = [
            {'name': 'OWS:TMS', 'type_label': 'TMS'},
            {'name': 'OWS:WMS-C', 'type_label': 'WMS-C'},
            {'name': 'OWS:WMTS', 'type_label': 'WMTS'},
            {'name': 'OWS:WCS', 'type_label': 'WCS'},
            {'name': 'OWS:WFS', 'type_label': 'WFS'},
            {'name': 'OWS:WMS', 'type_label': 'WMS'},
            {'name': 'OWS:WPS', 'type_label': 'WPS'},
            {'name': 'OWS:ALL', 'type_label': 'Any OWS'}
        ]
        # url
        url = f"{reverse('monitoring:api_event_types')}?{'ows_service=true'}"
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "event_types")
        resources = out["event_types"]
        for r in resources:
            self.assertIn(r, ows_events)

    def test_non_ows_events_enpoints(self):
        non_ows_events = [
            {'name': 'other', 'type_label': 'Not OWS'},
            {'name': 'all', 'type_label': 'All'},
            {'name': 'create', 'type_label': 'Create'},
            {'name': 'upload', 'type_label': 'Upload'},
            {'name': 'change', 'type_label': 'Change'},
            {'name': 'change_metadata', 'type_label': 'Change Metadata'},
            {'name': 'view_metadata', 'type_label': 'View Metadata'},
            {'name': 'view', 'type_label': 'View'},
            {'name': 'download', 'type_label': 'Download'},
            {'name': 'publish', 'type_label': 'Publish'},
            {'name': 'remove', 'type_label': 'Remove'},
            {'name': 'geoserver', 'type_label': 'Geoserver event'}
        ]
        # url
        url = f"{reverse('monitoring:api_event_types')}?{'ows_service=false'}"
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["errors"])
        self.assertEqual(out["data"]["key"], "event_types")
        resources = out["event_types"]
        for r in resources:
            self.assertIn(r, non_ows_events)

    def test_event_type_on_label_endpoint(self):
        events_on_label_data = [{'event_type': 'other',
                                 'max': '21.0000',
                                 'metric_count': 38,
                                 'min': '1.0000',
                                 'samples_count': 157,
                                 'sum': '157.0000',
                                 'val': 16},
                                {'event_type': 'all',
                                 'max': '3.0000',
                                 'metric_count': 25,
                                 'min': '1.0000',
                                 'samples_count': 31,
                                 'sum': '31.0000',
                                 'val': 14},
                                {'event_type': 'view',
                                 'max': '2.0000',
                                 'metric_count': 19,
                                 'min': '1.0000',
                                 'samples_count': 20,
                                 'sum': '20.0000',
                                 'val': 14},
                                {'event_type': 'upload',
                                 'max': '1.0000',
                                 'metric_count': 3,
                                 'min': '1.0000',
                                 'samples_count': 3,
                                 'sum': '3.0000',
                                 'val': 2},
                                {'event_type': 'view_metadata',
                                 'max': '1.0000',
                                 'metric_count': 2,
                                 'min': '1.0000',
                                 'samples_count': 2,
                                 'sum': '2.0000',
                                 'val': 2},
                                {'event_type': 'create',
                                 'max': '1.0000',
                                 'metric_count': 5,
                                 'min': '1.0000',
                                 'samples_count': 5,
                                 'sum': '5.0000',
                                 'val': 2},
                                {'event_type': 'download',
                                 'max': '1.0000',
                                 'metric_count': 1,
                                 'min': '1.0000',
                                 'samples_count': 1,
                                 'sum': '1.0000',
                                 'val': 1},
                                {'event_type': 'change_metadata',
                                 'max': '1.0000',
                                 'metric_count': 1,
                                 'min': '1.0000',
                                 'samples_count': 1,
                                 'sum': '1.0000',
                                 'val': 1}]
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'group_by=event_type_on_label'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 31536000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"][0]["data"]
        self.assertEqual(len(data), len(events_on_label_data))
        for d in data:
            self.assertIn(d, events_on_label_data)

    def test_event_type_on_user_endpoint(self):
        events_on_user_data = [
            {'event_type': 'all',
             'max': '3.0000',
             'metric_count': 25,
             'min': '1.0000',
             'samples_count': 31,
             'sum': '31.0000',
             'val': 5},
            {'event_type': 'other',
             'max': '21.0000',
             'metric_count': 38,
             'min': '1.0000',
             'samples_count': 157,
             'sum': '157.0000',
             'val': 5},
            {'event_type': 'view',
             'max': '2.0000',
             'metric_count': 19,
             'min': '1.0000',
             'samples_count': 20,
             'sum': '20.0000',
             'val': 5},
            {'event_type': 'view_metadata',
             'max': '1.0000',
             'metric_count': 2,
             'min': '1.0000',
             'samples_count': 2,
             'sum': '2.0000',
             'val': 2},
            {'event_type': 'upload',
             'max': '1.0000',
             'metric_count': 3,
             'min': '1.0000',
             'samples_count': 3,
             'sum': '3.0000',
             'val': 2},
            {'event_type': 'create',
             'max': '1.0000',
             'metric_count': 5,
             'min': '1.0000',
             'samples_count': 5,
             'sum': '5.0000',
             'val': 2},
            {'event_type': 'download',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'val': 1},
            {'event_type': 'change_metadata',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'val': 1}
        ]
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'group_by=event_type_on_user'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 31536000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"][0]["data"]
        self.assertEqual(len(data), len(events_on_user_data))
        for d in data:
            self.assertIn(d, events_on_user_data)

    def test_unique_visitors_count_endpoints(self):
        unique_visitors_data = [
            {
                'max': '3.0000',
                'metric_count': 25,
                'min': '1.0000',
                'samples_count': 31,
                'sum': '31.0000',
                'val': 5
            }
        ]
        # url
        url = f"{reverse('monitoring:api_metric_data', args={'request.users'})}?{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'group_by=user'}"
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            is_empty = [
                md for md in month_data if not (
                    md["max"]
                    or md["metric_count"]
                    or md["min"]
                    or md["samples_count"]
                    or md["sum"]
                    or md["val"]
                )
            ]
            if is_empty:
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(unique_visitors_data))
                for dd in month_data:
                    self.assertIn(dd, unique_visitors_data)
        self.assertEqual(empty_months, 11)

    def test_anonymous_sessions_count_endpoints(self):
        session_data = [
            {
                'max': '1.0000',
                'metric_count': 7,
                'min': '1.0000',
                'samples_count': 7,
                'sum': '7.0000',
                'val': 7
            }
        ]
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.users'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&&interval=2628000'}&{'group_by=label&user=AnonymousUser'}")
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            is_empty = [
                md for md in month_data if not (
                    md["max"]
                    or md["metric_count"]
                    or md["min"]
                    or md["samples_count"]
                    or md["sum"]
                    or md["val"]
                )
            ]
            if is_empty:
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(session_data))
                for dd in month_data:
                    self.assertIn(dd, session_data)
        self.assertEqual(empty_months, 11)

    def test_unique_visitors_list_endpoints(self):
        unique_visitors_data = [
            {
                'max': '1.0000',
                'metric_count': 7,
                'min': '1.0000',
                'samples_count': 7,
                'sum': '7.0000',
                'user': 'AnonymousUser',
                'val': 7
            },
            {
                'max': '1.0000',
                'metric_count': 5,
                'min': '1.0000',
                'samples_count': 5,
                'sum': '5.0000',
                'user': 'admin',
                'val': 3
            },
            {
                'max': '3.0000',
                'metric_count': 7,
                'min': '1.0000',
                'samples_count': 11,
                'sum': '11.0000',
                'user': 'joe',
                'val': 2
            },
            {
                'max': '1.0000',
                'metric_count': 3,
                'min': '1.0000',
                'samples_count': 3,
                'sum': '3.0000',
                'user': 'jhon',
                'val': 1
            },
            {
                'max': '2.0000',
                'metric_count': 3,
                'min': '1.0000',
                'samples_count': 5,
                'sum': '5.0000',
                'user': 'mary',
                'val': 1
            }
        ]
        # url
        url = f"{reverse('monitoring:api_metric_data', args={'request.users'})}?{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=2628000'}&{'group_by=user_on_label'}"
        # Unauthorized
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["data"]["metric"], 'request.users')
        self.assertEqual(out["data"]["interval"], 2628000)
        self.assertEqual(out["data"]["label"], None)
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["axis_label"], 'Count')
        self.assertEqual(out["data"]["type"], 'value')
        # # check data
        data = out["data"]["data"]
        self.assertEqual(len(data), 12)  # 12 months
        empty_months = 0
        for d in data:
            month_data = d["data"]
            if not len(month_data):
                empty_months += 1
            else:
                self.assertEqual(len(month_data), len(unique_visitors_data))
                for dd in month_data:
                    self.assertIn(dd, unique_visitors_data)
        self.assertEqual(empty_months, 11)

    def test_hostgeonode_cpu_endpoints(self):
        cpu_data = [
            {
                'label': '/proxy/?url=http%3A%2F%2Flocalhost%3A8080%2Fgeoserver%2Fows%3Fservice%3DWMS%26version'
                         '%3D1.1.1%26request%3DDescribeLayer%26layers%3Dgeonode%253Arailways%26access_token'
                         '%3DAGWnjcAoUtdfHP8XjuE5vEefu8j5sz',
                'max': '51.4624',
                'metric_count': 2,
                'min': '1.6354',
                'samples_count': 2,
                'sum': '53.0978',
                'user': None,
                'val': '26.5489000000000000'
            }
        ]
        url = (f"{reverse('monitoring:api_metric_data', args={'cpu.usage.percent'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'service=localhost-hostgeonode'}")
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        data = out["data"]
        self.assertEqual(data["metric"], "cpu.usage.percent")
        self.assertEqual(data["interval"], 31536000)
        self.assertEqual(data["label"], None)
        self.assertEqual(data["axis_label"], "%")
        self.assertEqual(data["type"], "rate")
        dd = data["data"][0]["data"]
        self.assertEqual(len(dd), len(cpu_data))
        for d in dd:
            self.assertIn(d, cpu_data)

    def test_hostgeoserver_cpu_endpoints(self):
        cpu_data = [
            {
                'label': '9d013cdaef339aedf8794f6558aacf4eaf5eddfaee11b6316b05105ea5b1968a',
                'max': '25.6353',
                'metric_count': 4,
                'min': '14.3133',
                'samples_count': 4,
                'sum': '75.3396',
                'user': 'AnonymousUser',
                'val': '18.8349000000000000'
            }
        ]
        url = (f"{reverse('monitoring:api_metric_data', args={'cpu.usage.percent'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'service=localhost-hostgeoserver'}")
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        data = out["data"]
        self.assertEqual(data["metric"], "cpu.usage.percent")
        self.assertEqual(data["interval"], 31536000)
        self.assertEqual(data["label"], None)
        self.assertEqual(data["axis_label"], "%")
        self.assertEqual(data["type"], "rate")
        dd = data["data"][0]["data"]
        self.assertEqual(len(dd), len(cpu_data))
        for d in dd:
            self.assertIn(d, cpu_data)

    def test_hostgeonode_mem_endpoints(self):
        mem_data = [
            {
                'label': '/layers/upload',
                'max': '88.7119',
                'metric_count': 3,
                'min': '75.1172',
                'samples_count': 3,
                'sum': '249.9528',
                'user': None,
                'val': '83.3176000000000000'
            }
        ]
        url = (f"{reverse('monitoring:api_metric_data', args={'mem.usage.percent'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'service=localhost-hostgeonode'}")
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        data = out["data"]
        self.assertEqual(data["metric"], "mem.usage.percent")
        self.assertEqual(data["interval"], 31536000)
        self.assertEqual(data["label"], None)
        self.assertEqual(data["axis_label"], "%")
        self.assertEqual(data["type"], "rate")
        dd = data["data"][0]["data"]
        self.assertEqual(len(dd), len(mem_data))
        for d in dd:
            self.assertIn(d, mem_data)

    def test_hostgeoserver_mem_endpoints(self):
        mem_data = [
            {
                'label': '/layers/upload',
                'max': '95.5952',
                'metric_count': 3,
                'min': '81.1286',
                'samples_count': 3,
                'sum': '269.5457',
                'user': None,
                'val': '89.8485666666666667'
            }
        ]
        url = (f"{reverse('monitoring:api_metric_data', args={'mem.usage.percent'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'service=localhost-hostgeoserver'}")
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        data = out["data"]
        self.assertEqual(data["metric"], "mem.usage.percent")
        self.assertEqual(data["interval"], 31536000)
        self.assertEqual(data["label"], None)
        self.assertEqual(data["axis_label"], "%")
        self.assertEqual(data["type"], "rate")
        dd = data["data"][0]["data"]
        self.assertEqual(len(dd), len(mem_data))
        for d in dd:
            self.assertIn(d, mem_data)

    def test_uptime_endpoints(self):
        uptime_data = [
            {
                'label': '9d013cdaef339aedf8794f6558aacf4eaf5eddfaee11b6316b05105ea5b1968a',
                'max': '17171.0000',
                'metric_count': 5,
                'min': '875.0000',
                'samples_count': 5,
                'sum': '36023.0000',
                'user': 'AnonymousUser',
                'val': '36023.0000'
            },
            {
                'label': '/proxy/?url=http%3A%2F%2Flocalhost%3A8080%2Fgeoserver%2Fows%3Fservice%3DWMS%26version'
                         '%3D1.1.1%26request%3DDescribeLayer%26layers%3Dgeonode%253Aroads%26access_token'
                         '%3DAGWnjcAoUtdfHP8XjuE5vEefu8j5sz',
                'max': '17167.7007',
                'metric_count': 5,
                'min': '874.4291',
                'samples_count': 5,
                'sum': '36012.0318',
                'user': None,
                'val': '36012.0318'
            }
        ]
        url = reverse('monitoring:api_metric_data', args={'uptime'})
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        data = out["data"]
        self.assertEqual(data["axis_label"], "s")
        self.assertEqual(data["interval"], 60.0)
        self.assertEqual(data["label"], None)
        self.assertEqual(data["metric"], "uptime")
        self.assertEqual(data["type"], "count")
        dd = data["data"][0]["data"]
        self.assertEqual(len(dd), len(uptime_data))
        for ud in dd:
            self.assertIn(ud, uptime_data)

    def test_hits_for_event_type_endpoint(self):
        # test data
        test_data = [
            {'event_type': 'other',
             'max': '24.0000',
             'metric_count': 17,
             'min': '1.0000',
             'samples_count': 165,
             'sum': '165.0000',
             'val': '165.0000'},
            {'event_type': 'all',
             'max': '4.0000',
             'metric_count': 16,
             'min': '1.0000',
             'samples_count': 31,
             'sum': '31.0000',
             'val': '31.0000'},
            {'event_type': 'view',
             'max': '4.0000',
             'metric_count': 10,
             'min': '1.0000',
             'samples_count': 20,
             'sum': '20.0000',
             'val': '20.0000'},
            {'event_type': 'create',
             'max': '1.0000',
             'metric_count': 5,
             'min': '1.0000',
             'samples_count': 5,
             'sum': '5.0000',
             'val': '5.0000'},
            {'event_type': 'upload',
             'max': '1.0000',
             'metric_count': 3,
             'min': '1.0000',
             'samples_count': 3,
             'sum': '3.0000',
             'val': '3.0000'},
            {'event_type': 'view_metadata',
             'max': '1.0000',
             'metric_count': 2,
             'min': '1.0000',
             'samples_count': 2,
             'sum': '2.0000',
             'val': '2.0000'},
            {'event_type': 'change_metadata',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'val': '1.0000'},
            {'event_type': 'download',
             'max': '1.0000',
             'metric_count': 1,
             'min': '1.0000',
             'samples_count': 1,
             'sum': '1.0000',
             'val': '1.0000'},
            {'event_type': 'OWS:ALL',
             'max': '0.0000',
             'metric_count': 17,
             'min': '0.0000',
             'samples_count': 0,
             'sum': '0.0000',
             'val': '0.0000'}
        ]
        # url
        url = f"{reverse('monitoring:api_metric_data', args={'request.count'})}?{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}&{'group_by=event_type'}"
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        data = out["data"]
        self.assertEqual(data["metric"], "request.count")
        self.assertEqual(data["interval"], 31536000)
        self.assertEqual(data["label"], None)
        self.assertEqual(data["axis_label"], "Count")
        self.assertEqual(data["type"], "count")
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        dd = data["data"][0]["data"]
        self.assertEqual(len(dd), len(test_data))
        for d in dd:
            self.assertIn(d, test_data)

    def test_countries_endpoint(self):
        # url
        url = (f"{reverse('monitoring:api_metric_data', args={'request.country'})}?"
               f"{'valid_from=2018-09-11T20:00:00.000Z&valid_to=2019-09-11T20:00:00.000Z&interval=31536000'}")
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        self.client.login_user(self.user)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        self.assertEqual(out["error"], "unauthorized_request")
        # Authorized
        self.client.login_user(self.admin)
        self.assertTrue(get_user(self.client).is_authenticated)
        response = self.client.get(url)
        out = json.loads(ensure_string(response.content))
        # Check data
        data = out["data"]
        self.assertEqual(data["metric"], "request.country")
        self.assertEqual(data["interval"], 31536000)
        self.assertEqual(data["label"], None)
        self.assertEqual(data["axis_label"], "Count")
        self.assertEqual(data["type"], "value")
        self.assertEqual(out["data"]["input_valid_from"], '2018-09-11T20:00:00.000000Z')
        self.assertEqual(out["data"]["input_valid_to"], '2019-09-11T20:00:00.000000Z')
        dd = data["data"][0]["data"]
        self.assertEqual(len(dd), 0)
