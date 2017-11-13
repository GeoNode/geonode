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

from datetime import datetime, timedelta

import os
from xml.etree.ElementTree import fromstring
import json
import xmljson
from decimal import Decimal
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core import mail

from geonode.contrib.monitoring.models import (RequestEvent, Host, Service, ServiceType,
                                               populate, ExceptionEvent, MetricNotificationCheck,
                                               MetricValue, NotificationCheck, Metric, OWSService,
                                               MonitoredResource, MetricLabel,
                                               NotificationMetricDefinition,)
from geonode.contrib.monitoring.models import do_autoconfigure

from geonode.contrib.monitoring.collector import CollectorAPI
from geonode.contrib.monitoring.utils import generate_periods, align_period_start
from geonode.base.populate_test_data import create_models
from geonode.layers.models import Layer


res_dir = os.path.join(os.path.dirname(__file__), 'resources')
req_err_path = os.path.join(res_dir, 'req_err.xml')
req_path = os.path.join(res_dir, 'req.xml')

req_err_xml = open(req_err_path, 'rt').read()
req_xml = open(req_path, 'rt').read()

req_big = xmljson.yahoo.data(fromstring(req_xml))
req_err_big = xmljson.yahoo.data(fromstring(req_err_xml))


class RequestsTestCase(TestCase):

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        create_models('layer')
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

        self.host = Host.objects.create(name='localhost', ip='127.0.0.1')
        self.service_type = ServiceType.objects.get(name=ServiceType.TYPE_GEONODE)
        self.service = Service.objects.create(name=settings.MONITORING_SERVICE_NAME,
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
        self.assertEqual(q[0].error_type, 'org.geoserver.platform.ServiceException')

    def test_gn_request(self):
        """
        Test if we have geonode requests logged
        """
        l = Layer.objects.all().first()
        self.client.login(username=self.user, password=self.passwd)
        self.client.get(reverse('layer_detail', args=(l.alternate,)), **{"HTTP_USER_AGENT": self.ua})

        self.assertEqual(RequestEvent.objects.all().count(), 1)
        rq = RequestEvent.objects.get()
        self.assertTrue(rq.response_time > 0)
        self.assertEqual(list(rq.resources.all().values_list('name', 'type')), [(l.alternate, u'layer',)])
        self.assertEqual(rq.request_method, 'GET')

    def test_gn_error(self):
        """
        Test if we get geonode errors logged
        """
        Layer.objects.all().first()
        self.client.login(username=self.user, password=self.passwd)
        self.client.get(reverse('layer_detail', args=('nonex',)), **{"HTTP_USER_AGENT": self.ua})

        RequestEvent.objects.get()
        self.assertEqual(RequestEvent.objects.all().count(), 1)

        self.assertEqual(ExceptionEvent.objects.all().count(), 1)
        eq = ExceptionEvent.objects.get()
        self.assertEqual('django.http.response.Http404', eq.error_type)

    def test_service_handlers(self):
        """
        Test if we can calculate metrics
        """
        self.client.login(username=self.user, password=self.passwd)
        for idx, l in enumerate(Layer.objects.all()):
            for inum in range(0, idx+1):
                self.client.get(reverse('layer_detail', args=(l.alternate,)), **{"HTTP_USER_AGENT": self.ua})
        requests = RequestEvent.objects.all()

        c = CollectorAPI()
        q = requests.order_by('created')
        c.process_requests(self.service, requests, q.last().created, q.first().created)
        interval = self.service.check_interval
        now = datetime.now()

        valid_from = now - (2*interval)
        valid_to = now

        self.assertTrue(isinstance(valid_from, datetime))
        self.assertTrue(isinstance(valid_to, datetime))
        self.assertTrue(isinstance(interval, timedelta))

        metrics = c.get_metrics_for(metric_name='request.ip',
                                    valid_from=valid_from,
                                    valid_to=valid_to,
                                    interval=interval)

        self.assertIsNotNone(metrics)


class MonitoringUtilsTestCase(TestCase):

    def test_time_periods(self):
        """
        Test if we can use time periods
        """
        # 2017-06-20 12:22:50
        start = datetime(year=2017, month=06, day=20, hour=12, minute=22, second=50)
        # 2017-06-20 12:20:00
        start_aligned = datetime(year=2017, month=06, day=20, hour=12, minute=20, second=0)
        interval = timedelta(minutes=5)
        # 12:22:50+ 0:05:20 = 12:27:02
        end = start + timedelta(minutes=5, seconds=22)

        expected_periods = [(start_aligned, start_aligned + interval,),
                            (start_aligned + interval, start_aligned + (2*interval),),
                            ]

        aligned = align_period_start(start, interval)
        self.assertEqual(start_aligned, aligned)

        periods = list(generate_periods(start, interval, end))
        self.assertEqual(expected_periods, periods)
        pnow = datetime.now()
        start_for_one = pnow - interval
        periods = list(generate_periods(start_for_one, interval, pnow))
        self.assertEqual(len(periods), 1)

        start_for_two = pnow - (2 * interval)
        periods = list(generate_periods(start_for_two, interval, pnow))
        self.assertEqual(len(periods), 2)

        start_for_three = pnow - (3 * interval)
        periods = list(generate_periods(start_for_three, interval, pnow))
        self.assertEqual(len(periods), 3)

        start_for_two_and_half = pnow - timedelta(seconds=(2.5 * interval.total_seconds()))
        periods = list(generate_periods(start_for_two_and_half, interval, pnow))
        self.assertEqual(len(periods), 3)


class MonitoringChecksTestCase(TestCase):

    reserved_fields = ('emails', 'severity', 'active', 'grace_period',)

    def setUp(self):
        super(MonitoringChecksTestCase, self).setUp()
        populate()
        self.host = Host.objects.create(name='localhost', ip='127.0.0.1')
        self.service_type = ServiceType.objects.get(name=ServiceType.TYPE_GEONODE)
        self.service = Service.objects.create(name=settings.MONITORING_SERVICE_NAME,
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
        start = datetime.now()
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval
        # sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        ows_service = OWSService.objects.get(name='WFS')
        resource, _ = MonitoredResource.objects.get_or_create(type='layer', name='test:test')
        resource2, _ = MonitoredResource.objects.get_or_create(type='layer', name='test:test2')

        label, _ = MetricLabel.objects.get_or_create(name='discount')
        MetricValue.add(self.metric, start_aligned,
                        end_aligned, self.service,
                        label="Count",
                        value_raw=10,
                        value_num=10,
                        value=10)
        uthreshold = [(self.metric.name, 'min_value', False, False, False, False,
                       0, 100, None, "Min number of request"),
                      (self.metric.name, 'max_value', False, False, False, False,
                       1000, None, None, "Max number of request"),
                      ]
        notification_data = {'name': 'check requests name',
                             'description': 'check requests description',
                             'severity': 'warning',
                             'user_threshold': uthreshold}
        nc = NotificationCheck.create(**notification_data)
        mc = MetricNotificationCheck.objects.create(notification_check=nc,
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
                        ows_service=ows_service)

        mc.min_value = 11
        mc.max_value = None
        mc.ows_service = ows_service
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
        mc.ows_service = None
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

        start = datetime.now()
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval

        # sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        resource, _ = MonitoredResource.objects.get_or_create(type='layer', name='test:test')
        resource2, _ = MonitoredResource.objects.get_or_create(type='layer', name='test:test2')

        label, _ = MetricLabel.objects.get_or_create(name='discount')
        MetricValue.add(self.metric, start_aligned, end_aligned, self.service,
                        label="Count",
                        value_raw=10,
                        value_num=10,
                        value=10)
        nc = NotificationCheck.objects.create(name='check requests', description='check requests')

        MetricNotificationCheck.objects.create(notification_check=nc,
                                               service=self.service,
                                               metric=self.metric,
                                               min_value=10,
                                               max_value=200,
                                               resource=resource,
                                               max_timeout=None)

        c = self.client
        c.login(username=self.user, password=self.passwd)
        nresp = c.get(reverse('monitoring:api_user_notifications'))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(data['data'][0]['id'] == nc.id)

        nresp = c.get(reverse('monitoring:api_user_notification_config', kwargs={'pk': nc.id}))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(data['data']['notification']['id'] == nc.id)

        nresp = c.get(reverse('monitoring:api_user_notifications'))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(data['data'][0]['id'] == nc.id)

        c.login(username=self.user2, password=self.passwd2)
        nresp = c.get(reverse('monitoring:api_user_notifications'))
        self.assertEqual(nresp.status_code, 200)
        data = json.loads(nresp.content)
        self.assertTrue(len(data['data']) == 1)

    def test_notifications_edit_views(self):

        start = datetime.now()
        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval

        # sanity check
        self.assertTrue(start_aligned < start < end_aligned)

        resource, _ = MonitoredResource.objects.get_or_create(type='layer', name='test:test')

        label, _ = MetricLabel.objects.get_or_create(name='discount')

        c = self.client
        c.login(username=self.user, password=self.passwd)
        notification_url = reverse('monitoring:api_user_notifications')
        uthreshold = [('request.count', 'min_value', False, False, False, False,
                       0, 100, None, "Min number of request"),
                      ('request.count', 'max_value', False, False, False, False,
                       1000, None, None, "Max number of request"),
                      ]
        notification_data = {'name': 'test',
                             'description': 'more test',
                             'severity': 'warning',
                             'user_threshold': json.dumps(uthreshold)}

        out = c.post(notification_url, notification_data)
        self.assertEqual(out.status_code, 200)

        jout = json.loads(out.content)
        nid = jout['data']['id']
        ndef = NotificationMetricDefinition.objects.filter(notification_check__id=nid)
        self.assertEqual(ndef.count(), 2)

        notification_url = reverse('monitoring:api_user_notification_config', kwargs={'pk': nid})
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

        out = c.post(notification_url, json.dumps(notification_data), content_type='application/json')
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
        start = datetime.now()

        start_aligned = align_period_start(start, self.service.check_interval)
        end_aligned = start_aligned + self.service.check_interval

        # for (metric_name, field_opt, use_service,
        #     use_resource, use_label, use_ows_service,
        #     minimum, maximum, thresholds,) in thresholds:

        notifications_config = ('geonode is not working',
                                'detects when requests are not handled',
                                (('request.count', 'min_value', False, False,
                                 False, False, 0, 10, None, 'Number of handled requests is lower than',),
                                 ('response.time', 'max_value', False, False,
                                  False, False, 500, None, None, 'Response time is higher than',),))
        nc = NotificationCheck.create(*notifications_config)
        self.assertTrue(nc.definitions.all().count() == 2)

        user = self.u2
        pwd = self.passwd2

        self.client.login(username=user.username, password=pwd)
        for nc in NotificationCheck.objects.all():
            notifications_config_url = reverse('monitoring:api_user_notification_config', args=(nc.id,))
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

            self.assertEqual(resp.status_code, 400)

            vals = [7, 600]
            data = {'emails': '\n'.join([self.u.email, self.u2.email, 'testsome@test.com'])}
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
            self.assertEqual(set([u.email for u in nc.get_users()]), set(_users))
            self.assertEqual(set([email for email in nc.get_emails()]), set(_emails))

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
        self.assertTrue(nc.receivers.all().count() > 0)
        self.assertEqual(len(mail.outbox), nc.receivers.all().count())

        nc.refresh_from_db()
        notifications_url = reverse('monitoring:api_user_notifications')
        nresp = self.client.get(notifications_url)
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


class AutoConfigTestCase(TestCase):
    OGC_GS_1 = 'http://localhost/geoserver123/'
    OGC_GS_2 = 'http://google.com/test/'

    OGC_SERVER = {'default': {'BACKEND': 'nongeoserver'},
                  'geoserver1': {'BACKEND': 'geonode.geoserver', 'LOCATION': OGC_GS_1},
                  'external1': {'BACKEND': 'geonode.geoserver', 'LOCATION': OGC_GS_2}
                  }

    def setUp(self):
        super(AutoConfigTestCase, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.is_superuser = True
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
        self.client.login(username=self.user, password=self.passwd)

        resp = self.client.post(autoconf_url)
        self.assertEqual(resp.status_code, 200)
