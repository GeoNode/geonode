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
import os
import pytz
import queue
import logging
import xmljson
import requests
import threading
import traceback

from hashlib import md5
from math import floor, ceil
from urllib.parse import urlencode
from urllib.parse import urlsplit
from bs4 import BeautifulSoup as bs
from dateutil.tz import tzlocal
from datetime import datetime, timedelta
from owslib.etree import etree as dlxml

from django.conf import settings
from django.db.models.fields.related import RelatedField

from geonode.tasks.tasks import AcquireLock
from geonode.settings import DATETIME_INPUT_FORMATS

GS_FORMAT = "%Y-%m-%dT%H:%M:%S"  # 2010-06-20T2:00:00

log = logging.getLogger(__name__)


class MonitoringHandler(logging.Handler):
    def __init__(self, service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = service

    def emit(self, record):
        from geonode.monitoring.models import RequestEvent, ExceptionEvent

        exc_info = record.exc_info
        req = record.request
        resp = record.response
        if not req._monitoring.get("processed"):
            try:
                re = RequestEvent.from_geonode(self.service, req, resp)
                req._monitoring["processed"] = re
            except Exception:
                req._monitoring["processed"] = None
        re = req._monitoring.get("processed")

        if re and exc_info:
            tb = traceback.format_exception(*exc_info)
            ExceptionEvent.add_error(self.service, exc_info[1], tb, request=re)


class RequestToMonitoringThread(threading.Thread):
    q = queue.Queue()

    def __init__(self, service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = service

    def add(self, req, resp):
        item = (
            req,
            resp,
        )
        RequestToMonitoringThread.q.put(item)

    def run(self):
        from geonode.monitoring.models import RequestEvent

        q = RequestToMonitoringThread.q
        while True:
            if not q.empty():
                item = q.get()
                req, resp = item
                RequestEvent.from_geonode(self.service, req, resp)


class GeoServerMonitorClient:
    REPORT_FORMATS = (
        "html",
        "xml",
        "json",
    )

    def __init__(self, base_url):
        self.base_url = base_url

    def get_href(self, link, format=None):
        href = urlsplit(link["href"])
        base_url = urlsplit(self.base_url)
        if href and href.netloc != base_url.netloc:
            href = href._replace(netloc=base_url.netloc)
            href = href._replace(scheme=base_url.scheme)
        if format is None:
            return href.geturl()
        if format in self.REPORT_FORMATS:
            href, ext = os.path.splitext(href.geturl())
            return f"{href}.{format}"
        return format

    def get_requests(self, format=None, since=None, until=None):
        """
        Returns list of requests from monitoring
        """
        from requests.auth import HTTPBasicAuth

        rest_url = f"{self.base_url}rest/monitor/requests.html"
        qargs = {}
        if since:
            # since = since.astimezone(utc)
            qargs["from"] = since.strftime(GS_FORMAT)
        if until:
            # until = until.astimezone(utc)
            qargs["to"] = until.strftime(GS_FORMAT)
        if qargs:
            rest_url = f"{rest_url}?{urlencode(qargs)}"

        log.debug("checking", rest_url)
        username = settings.OGC_SERVER["default"]["USER"]
        password = settings.OGC_SERVER["default"]["PASSWORD"]
        resp = requests.get(rest_url, auth=HTTPBasicAuth(username, password), timeout=30, verify=False)
        doc = bs(resp.content, features="lxml")
        links = doc.find_all("a")
        for lyr in links:
            href = self.get_href(lyr, format)
            data = self.get_request(href, format=format)
            if data:
                yield data
            else:
                log.warning(f"Skipping payload for {href}")

    def get_request(self, href, format=format):
        from requests.auth import HTTPBasicAuth

        username = settings.OGC_SERVER["default"]["USER"]
        password = settings.OGC_SERVER["default"]["PASSWORD"]
        log.debug(f" href: {href} ")
        r = requests.get(href, auth=HTTPBasicAuth(username, password), timeout=30, verify=False)
        if r.status_code != 200:
            log.warning("Invalid response for %s: %s", href, r)
            return
        data = None
        try:
            data = r.json()
        except (
            ValueError,
            TypeError,
        ):
            # traceback.print_exc()
            try:
                data = dlxml.fromstring(r.content)
            except Exception as err:
                log.debug("Cannot parse xml contents for %s: %s", href, err, exc_info=err)
                data = bs(r.content)
        if len(data) and format != "json":
            return self.to_json(data, format)
        return data

    def _from_xml(self, val):
        try:
            return xmljson.yahoo.data(val)
        except Exception:
            # raise ValueError("Cannot convert from val %s" % val)
            pass

    def _from_html(self, val):
        raise ValueError("Cannot convert from html")

    def to_json(self, data, from_format):
        h = getattr(self, f"_from_{from_format}", None)
        if not h or not len(data):
            raise ValueError(f"Cannot convert from {from_format} - no handler")
        return h(data)


def align_period_end(end, interval):
    utc = pytz.utc
    day_end = datetime(*end.date().timetuple()[:6]).replace(tzinfo=utc)
    # timedelta
    diff = end - day_end
    # seconds
    diff_s = diff.total_seconds()
    int_s = interval.total_seconds()
    # rounding to last lower full period
    interval_num = ceil(diff_s / float(int_s))

    return day_end + timedelta(seconds=(interval_num * interval.total_seconds()))


def align_period_start(start, interval):
    utc = pytz.utc
    day_start = datetime(*start.date().timetuple()[:6]).replace(tzinfo=utc)
    # timedelta
    diff = start.replace(tzinfo=utc) - day_start
    # seconds
    diff_s = diff.total_seconds()
    int_s = interval.total_seconds()
    # rounding to last lower full period
    interval_num = floor(diff_s / float(int_s))

    return day_start + timedelta(seconds=(interval_num * interval.total_seconds()))


def generate_periods(since, interval, end=None, align=True):
    """
    Generator of periods: tuple of [start, end).
    since parameter will be aligned to closest interval before since.
    """
    utc = pytz.utc
    end = end or datetime.utcnow().replace(tzinfo=utc)
    if align:
        since_aligned = align_period_start(since, interval)
    else:
        since_aligned = since
    if end < since:
        raise ValueError("End cannot be earlienr than beginning")
    full_interval = (end - since).total_seconds()
    _periods = divmod(full_interval, interval.total_seconds())
    periods_count = _periods[0]
    if _periods[1]:
        periods_count += 1

    end = since_aligned + timedelta(seconds=(periods_count * interval.total_seconds()))

    while since_aligned < end:
        yield (
            since_aligned,
            since_aligned + interval,
        )
        since_aligned = since_aligned + interval


class TypeChecks:
    AUDIT_TYPE_JSON = "json"
    AUDIT_TYPE_XML = "xml"
    AUDIT_FORMATS = (
        AUDIT_TYPE_JSON,
        AUDIT_TYPE_XML,
    )

    @classmethod
    def audit_format(cls, val):
        if val not in cls.AUDIT_FORMATS:
            raise ValueError(f"Invalid value for audit format: {val}")
        return val

    @staticmethod
    def host_type(val):
        from geonode.monitoring.models import Host

        try:
            return Host.objects.get(name=val)
        except Host.DoesNotExist:
            raise ValueError(f"Host {val} does not exist")

    @staticmethod
    def resource_type(val):
        from geonode.monitoring.models import MonitoredResource

        try:
            val = int(val)
            return MonitoredResource.objects.get(id=val)
        except (
            ValueError,
            TypeError,
        ):
            try:
                rtype, rname = val.split("=")
            except (
                ValueError,
                IndexError,
            ):
                raise ValueError(f"{val} is not valid resource description")
        return MonitoredResource.objects.get(type=rtype, name=rname)

    @staticmethod
    def resource_type_type(val):
        from geonode.monitoring.models import MonitoredResource

        if val in MonitoredResource._TYPES:
            return val
        raise ValueError(f"Invalid monitored resource type: {val}")

    @staticmethod
    def metric_name_type(val):
        from geonode.monitoring.models import Metric

        try:
            return Metric.objects.get(name=val)
        except Metric.DoesNotExist:
            raise ValueError(f"Metric {val} doesn't exist")

    @staticmethod
    def service_type(val):
        from geonode.monitoring.models import Service

        try:
            return Service.objects.get(name=val)
        except Service.DoesNotExist:
            raise ValueError(f"Service {val} does not exist")

    @staticmethod
    def service_type_type(val):
        from geonode.monitoring.models import ServiceType

        try:
            return ServiceType.objects.get(name=val)
        except ServiceType.DoesNotExist:
            raise ValueError(f"Service Type {val} does not exist")

    @staticmethod
    def label_type(val):
        from geonode.monitoring.models import MetricLabel

        try:
            return MetricLabel.objects.get(id=val)
        except (
            ValueError,
            TypeError,
            MetricLabel.DoesNotExist,
        ):
            try:
                return MetricLabel.objects.get(name=val)
            except MetricLabel.DoesNotExist:
                pass
        raise ValueError(f"Invalid label value: {val}")

    @staticmethod
    def user_type(val):
        from geonode.monitoring.models import MetricLabel

        try:
            if MetricLabel.objects.filter(user=val).count():
                return val
        except MetricLabel.DoesNotExist:
            raise ValueError(f"Invalid user value: {val}")

    @staticmethod
    def event_type_type(val):
        from geonode.monitoring.models import EventType

        try:
            return EventType.objects.get(name=val)
        except EventType.DoesNotExist:
            raise ValueError(f"Event Type {val} doesn't exist")

    @staticmethod
    def ows_service_type(val):
        if str(val).lower() in ("true", "1"):
            return True
        elif str(val).lower() in ("false", "0"):
            return False
        else:
            raise ValueError(f"Invalid ows_service value {val}")


def dump(obj, additional_fields=tuple()):
    if hasattr(obj, "_meta"):
        fields = obj._meta.fields
    else:
        fields = []
    out = {}
    for field in fields:
        fname = field.name
        val = getattr(obj, fname)
        if isinstance(field, RelatedField):
            if val is not None:
                v = val
                val = {"class": f"{val.__class__.__module__}.{val.__class__.__name__}", "id": val.pk}
                if hasattr(v, "name"):
                    val["name"] = v.name
        if isinstance(val, timedelta):
            val = {"class": "datetime.timedelta", "seconds": val.total_seconds()}
        out[fname] = val
    for fname in additional_fields:
        val = getattr(obj, fname, None)
        if isinstance(val, timedelta):
            val = {"class": "datetime.timedelta", "seconds": val.total_seconds()}
        out[fname] = val
    return out


def extend_datetime_input_formats(formats):
    """
    Add new DateTime input formats
    :param formats: input formats yoy want to add (tuple or list)
    :return: extended input formats
    """
    input_formats = DATETIME_INPUT_FORMATS
    if isinstance(input_formats, tuple):
        input_formats += tuple(formats)
    elif isinstance(input_formats, list):
        input_formats.extend(formats)
    else:
        raise ValueError("Input parameter must be tuple or list.")
    return input_formats


def collect_metric(**options):
    # Exit early if MONITORING_ENABLED=False
    if not settings.MONITORING_ENABLED:
        return

    # Avoid possible module circular dependency issues
    from geonode.monitoring.models import Service
    from geonode.monitoring.collector import CollectorAPI

    _start_time = None
    _end_time = None
    # The cache key consists of the task name and the MD5 digest
    # of the name.
    name = b"collect_metric"
    hexdigest = md5(name).hexdigest()
    lock_id = f"{name.decode()}-lock-{hexdigest}"
    _start_time = _end_time = datetime.utcnow().isoformat()
    log.info(f"[{lock_id}] Collecting Metrics - started @ {_start_time}")
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                log.info(f"[{lock_id}] Collecting Metrics - [...acquired lock] @ {_start_time}")
                try:
                    oservice = options["service"]
                    if not oservice:
                        services = Service.objects.all()
                    else:
                        services = [oservice]
                    if options["list_services"]:
                        print("available services")
                        for s in services:
                            print("  ", s.name, "(", s.url, ")")
                            print("   type", s.service_type.name)
                            print("   running on", s.host.name, s.host.ip)
                            print("   active:", s.active)
                            if s.last_check:
                                print("    last check:", s.last_check)
                            else:
                                print("    not checked yet")
                            print(" ")
                        return
                    c = CollectorAPI()
                    for s in services:
                        try:
                            run_check(
                                s,
                                collector=c,
                                since=options["since"],
                                until=options["until"],
                                force_check=options["force_check"],
                                format=options["format"],
                            )
                        except Exception as e:
                            log.warning(e)
                    if not options["do_not_clear"]:
                        log.info("Clearing old data")
                        c.clear_old_data()
                    if options["emit_notifications"]:
                        log.info("Processing notifications for %s", options["until"])
                        # s = Service.objects.first()
                        # interval = s.check_interval
                        # now = datetime.utcnow().replace(tzinfo=pytz.utc)
                        # notifications_check = now - interval
                        c.emit_notifications()  # notifications_check))
                    _end_time = datetime.utcnow().isoformat()
                    log.info(f"[{lock_id}] Collecting Metrics - finished @ {_end_time}")
                except Exception as e:
                    log.info(f"[{lock_id}] Collecting Metrics - errored @ {_end_time}")
                    log.exception(e)
            finally:
                lock.release()

    log.info(f"[{lock_id}] Collecting Metrics - exit @ {_end_time}")
    return (_start_time, _end_time)


def run_check(service, collector, since=None, until=None, force_check=None, format=None):
    from geonode.monitoring.service_handlers import get_for_service

    utc = pytz.utc
    try:
        local_tz = pytz.timezone(datetime.now(tzlocal()).tzname())
    except Exception:
        local_tz = pytz.timezone(settings.TIME_ZONE)
    now = datetime.utcnow().replace(tzinfo=utc)
    Handler = get_for_service(service.service_type.name)
    try:
        service.last_check = service.last_check.astimezone(utc)
    except Exception:
        service.last_check = service.last_check.replace(tzinfo=utc) if service.last_check else now

    if not until:
        until = now
    else:
        until = local_tz.localize(until).astimezone(utc).replace(tzinfo=utc)

    last_check = local_tz.localize(since).astimezone(utc).replace(tzinfo=utc) if since else service.last_check
    _monitoring_ttl_max = timedelta(days=365) if force_check else settings.MONITORING_DATA_TTL
    if not last_check or last_check > until or (until - last_check) > _monitoring_ttl_max:
        last_check = until - _monitoring_ttl_max
        service.last_check = last_check

    # print('[',now ,'] checking', service.name, 'since', last_check, 'until', until)
    data_in = None
    h = Handler(service, force_check=force_check)
    data_in = h.collect(since=last_check, until=until, format=format)
    if data_in:
        try:
            return collector.process(service, data_in, last_check, until)
        finally:
            h.mark_as_checked()
