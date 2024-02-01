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
import logging
import re
import pytz
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain

from django.conf import settings
from django.db import models
from django.utils.html import strip_tags
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives as EmailMessage
from django.utils.translation import gettext_noop as _
from django.db.models import Max
from django.urls import resolve, Resolver404


from geonode.utils import raw_sql
from geonode.notifications_helper import send_notification
from geonode.monitoring.apps import MonitoringAppConfig as AppConf
from geonode.monitoring.models import (
    Metric,
    MetricValue,
    RequestEvent,
    MonitoredResource,
    ExceptionEvent,
    EventType,
    NotificationCheck,
    BuiltIns,
)

from geonode.monitoring.utils import generate_periods, align_period_start, align_period_end
from geonode.monitoring.aggregation import (
    aggregate_past_periods,
    calculate_rate,
    calculate_percent,
    extract_resources,
    extract_event_type,
    extract_event_types,
    extract_special_event_types,
    get_resources_for_metric,
    get_labels_for_metric,
    get_metric_names,
)
from geonode.base.models import ResourceBase
from geonode.utils import parse_datetime


log = logging.getLogger(__name__)


class CollectorAPI:
    def __init__(self):
        pass

    def _calculate_rate(self, metric_name, metric_label, current_value, valid_to):
        """
        Find previous network metric value and calculate rate between them
        """
        return calculate_rate(metric_name, metric_label, current_value, valid_to)

    def _calculate_percent(self, metric_name, metric_label, current_value, valid_to):
        """
        Find previous network metric value and calculate percent
        """
        return calculate_percent(metric_name, metric_label, current_value, valid_to)

    def process_host_geoserver(self, service, data, valid_from, valid_to):
        """
        Generates mertic values for system-level measurements
        """
        desc_re = re.compile(r"\[(\w+)\]")

        def get_iface_name(row):
            desc = row["description"]
            m = desc_re.search(desc)
            if m is None:
                return
            return m.groups()[0]

        def get_network_rate(row, value, metric_defaults, metric_name, valid_to):
            iface_label = get_iface_name(row)
            if not iface_label:
                try:
                    log.debug("no label", metric_name, row.get("description"))
                except Exception:
                    pass
                return
            rate = self._calculate_rate(metric_name, iface_label, value, valid_to)
            if rate is None:
                try:
                    log.debug("no rate for", metric_name)
                except Exception:
                    pass
                return
            mdata = {
                "value": rate,
                "value_raw": rate,
                "value_num": rate,
                "label": iface_label,
                "metric": f"{metric_name}.rate",
            }
            mdata.update(metric_defaults)
            log.debug(MetricValue.add(**mdata))

        def get_mem_label(*args):
            return "B"

        # gs metric -> monitoring metric name, label function, postproc
        # function
        GS_METRIC_MAP = dict(
            (
                (
                    "SYSTEM_UPTIME",
                    (
                        "uptime",
                        None,
                        None,
                    ),
                ),
                (
                    "SYSTEM_AVERAGE_LOAD",
                    (
                        "load.1m",
                        None,
                        None,
                    ),
                ),
                (
                    "CPU_LOAD",
                    (
                        "cpu.usage.percent",
                        None,
                        None,
                    ),
                ),
                (
                    "MEMORY_USED",
                    (
                        "mem.usage.percent",
                        get_mem_label,
                        None,
                    ),
                ),
                (
                    "MEMORY_TOTAL",
                    (
                        "mem.all",
                        get_mem_label,
                        None,
                    ),
                ),
                (
                    "MEMORY_FREE",
                    (
                        "mem.free",
                        get_mem_label,
                        None,
                    ),
                ),
                (
                    "NETWORK_INTERFACE_SEND",
                    ("network.out", get_iface_name, get_network_rate),
                ),
                (
                    "NETWORK_INTERFACE_RECEIVED",
                    ("network.in", get_iface_name, get_network_rate),
                ),
                (
                    "NETWORK_INTERFACES_SEND",
                    ("network.out", None, get_network_rate),
                ),
                (
                    "NETWORK_INTERFACES_RECEIVED",
                    ("network.in", None, get_network_rate),
                ),
            )
        )

        utc = pytz.utc
        collected_at = datetime.utcnow().replace(tzinfo=utc)

        valid_from = align_period_start(collected_at, service.check_interval)
        valid_to = align_period_end(collected_at, service.check_interval)

        mdefaults = {
            "valid_from": valid_from,
            "valid_to": valid_to,
            "resource": None,
            "samples_count": 1,
            "service": service,
        }

        metrics = [m[0] for m in GS_METRIC_MAP.values()]

        MetricValue.objects.filter(
            service_metric__metric__name__in=metrics, valid_from=valid_from, valid_to=valid_to, service=service
        ).delete()

        for metric_data in data:
            map_data = GS_METRIC_MAP.get(metric_data["name"])
            if not map_data:
                continue
            metric_name, label_function, processing_function = map_data
            if metric_name is None:
                continue
            value = metric_data["value"]
            if isinstance(value, str):
                value = value.replace(",", ".")
            mdata = {
                "value": value,
                "value_raw": value,
                "value_num": value,
                "label": label_function(metric_data) if callable(label_function) else None,
                "metric": metric_name,
            }
            mdata.update(mdefaults)
            log.debug(MetricValue.add(**mdata))

            if callable(processing_function):
                processing_function(metric_data, value, mdefaults, metric_name, valid_to)

    def process_host_geonode(self, service, data, valid_from, valid_to):
        """
        Generates mertic values for system-level measurements
        """
        utc = pytz.utc
        import dateutil.parser

        collected_at = parse_datetime(dateutil.parser.parse(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")).replace(
            tzinfo=utc
        )
        valid_from = align_period_start(collected_at, service.check_interval)
        valid_to = align_period_end(collected_at, service.check_interval)
        mdefaults = {
            "valid_from": valid_from,
            "valid_to": valid_to,
            "resource": None,
            "samples_count": 1,
            "service": service,
        }

        MetricValue.objects.filter(
            service_metric__metric__name__in=("network.in", "network.out"),
            valid_from=valid_from,
            valid_to=valid_to,
            service=service,
        ).delete()

        for ifname, ifdata in data["data"]["network"].items():
            for tx_label, tx_value in ifdata["traffic"].items():
                mdata = {
                    "value": tx_value,
                    "value_raw": tx_value,
                    "value_num": tx_value,
                    "label": ifname,
                    "metric": f"network.{tx_label}",
                }
                mdata.update(mdefaults)
                rate = self._calculate_rate(mdata["metric"], ifname, tx_value, valid_to)
                log.debug(MetricValue.add(**mdata))
                if rate:
                    mdata["metric"] = f"{mdata['metric']}.rate"
                    mdata["value"] = rate
                    mdata["value_num"] = rate
                    mdata["value_raw"] = rate
                    log.debug(MetricValue.add(**mdata))

        ldata = data["data"]["load"]
        llabel = ["1", "5", "15"]

        memory_info = data["data"]["memory"]
        mkeys = [m.name[len("mem.") :] for m in service.get_metrics() if m.name.startswith("mem.")]
        for mkey in mkeys:
            mdata = memory_info.get(mkey)
            if not mdata:
                continue
            mdata = {
                "value": mdata,
                "value_raw": mdata,
                "value_num": mdata,
                "metric": f"mem.{mkey}",
                "label": "B",
            }
            mdata.update(mdefaults)
            MetricValue.objects.filter(
                service_metric__metric__name=mdata["metric"],
                valid_from=mdata["valid_from"],
                valid_to=mdata["valid_to"],
                label__name="MB",
                service=service,
            ).delete()
            log.debug(MetricValue.add(**mdata))

        MetricValue.objects.filter(
            service_metric__metric__name__in=(
                "storage.total",
                "storage.used",
                "storage.free",
            ),
            valid_from=valid_from,
            valid_to=valid_to,
            service=service,
        ).delete()

        for df in data["data"]["disks"]:
            # dev = df['device']
            total = df["total"]
            used = df["used"]
            free = df["free"]
            # free_pct = df['percent']
            mount = df["mountpoint"]
            for metric, val in (
                (
                    "storage.total",
                    total,
                ),
                (
                    "storage.used",
                    used,
                ),
                (
                    "storage.free",
                    free,
                ),
            ):
                mdata = {
                    "value": val,
                    "value_raw": val,
                    "value_num": val,
                    "metric": metric,
                    "label": mount,
                }
                mdata.update(mdefaults)
                log.debug(MetricValue.add(**mdata))

        if ldata:
            for lidx, l in enumerate(ldata):
                mdata = {
                    "value": l,
                    "value_raw": l,
                    "value_num": l,
                    "metric": f"load.{llabel[lidx]}m",
                    "label": "Value",
                }

                mdata.update(mdefaults)
                MetricValue.objects.filter(
                    service_metric__metric__name=mdata["metric"],
                    valid_from=mdata["valid_from"],
                    valid_to=mdata["valid_to"],
                    label__name="Value",
                    service=service,
                ).delete()
                log.debug(MetricValue.add(**mdata))

        uptime = data["data"].get("uptime")
        if uptime is not None:
            mdata = {"value": uptime, "value_raw": uptime, "value_num": uptime, "metric": "uptime", "label": "Seconds"}
            mdata.update(mdefaults)
            MetricValue.objects.filter(
                service_metric__metric__name=mdata["metric"],
                valid_from=mdata["valid_from"],
                valid_to=mdata["valid_to"],
                label__name=mdata["label"],
                service=service,
            ).delete()
            log.debug(MetricValue.add(**mdata))

        if data["data"].get("cpu"):
            _l = data["data"]["cpu"]["usage"]
            mdata = {
                "value": _l,
                "value_raw": _l,
                "value_num": _l,
                "metric": "cpu.usage",
                "label": "Seconds",
            }

            mdata.update(mdefaults)

            MetricValue.objects.filter(
                service_metric__metric__name=mdata["metric"],
                valid_from=mdata["valid_from"],
                valid_to=mdata["valid_to"],
                label__name=mdata["label"],
                service=service,
            ).delete()
            log.debug(MetricValue.add(**mdata))
            rate = self._calculate_rate(mdata["metric"], mdata["label"], mdata["value"], mdata["valid_to"])
            if rate:
                rate_data = mdata.copy()
                rate_data["metric"] = f"{mdata['metric']}.rate"
                rate_data["value"] = rate
                rate_data["value_num"] = rate
                rate_data["value_raw"] = rate
                log.debug(MetricValue.add(**rate_data))

            percent = self._calculate_percent(mdata["metric"], mdata["label"], mdata["value"], mdata["valid_to"])
            if percent:
                percent_data = mdata.copy()
                percent_data["metric"] = f"{mdata['metric']}.percent"
                percent_data["value"] = percent
                percent_data["value_num"] = percent
                percent_data["value_raw"] = percent
                percent_data["label"] = "Value"
                log.debug(MetricValue.add(**percent_data))

            mdata.update(mdefaults)
            log.debug(MetricValue.add(**mdata))

    def get_labels_for_metric(self, metric_name, resource=None):
        return get_labels_for_metric(metric_name, resource)

    def get_resources_for_metric(self, metric_name):
        return get_resources_for_metric(metric_name)

    def get_metric_names(self):
        """
        Returns list of tuples: (service type, list of metrics)
        """
        return get_metric_names()

    def extract_resources(self, requests):
        return extract_resources(requests)

    def extract_event_type(self, requests):
        return extract_event_type(requests)

    def extract_event_types(self, requests):
        return extract_event_types(requests)

    def extract_special_event_types(self, requests):
        """
        Return list of pairs (event_type, requests)
        that should be registered as one of aggregating event types: ows:all, other,
        """
        return extract_special_event_types(requests)

    def set_metric_values(self, metric_name, column_name, requests, service, **metric_values):
        metric = Metric.get_for(metric_name, service=service)

        def _key(v):
            return v["value"]

        # we need list of three items:
        #  * value - numeric value for given metric
        #  * label - label value to be used
        #  * samples count - number of samples for a metric
        if metric.is_rate:
            row = requests.aggregate(value=models.Avg(column_name))
            row["samples"] = requests.count()
            row["label"] = Metric.TYPE_RATE
            q = [row]
        elif metric.is_count:
            q = []
            values = requests.distinct(column_name).values_list(column_name, flat=True)
            for v in values:
                rqs = requests.filter(**{column_name: v})
                row = rqs.aggregate(value=models.Sum(column_name), samples=models.Count(column_name))
                row["label"] = v
                q.append(row)
            q.sort(key=_key)
            q.reverse()
        elif metric.is_value:
            q = []
            is_user_metric = column_name == "user_identifier"
            if is_user_metric:
                values = requests.distinct(column_name).values_list(column_name, "user_username")
            else:
                values = requests.distinct(column_name).values_list(column_name, flat=True)
            for v in values:
                if v is not None:
                    value = v
                    if is_user_metric:
                        value = v[0]
                    rqs = requests.filter(**{column_name: value})
                    row = rqs.aggregate(value=models.Count(column_name), samples=models.Count(column_name))
                    row["label"] = v
                    q.append(row)
            q.sort(key=_key)
            q.reverse()
        elif metric.is_value_numeric:
            q = []
            row = requests.aggregate(value=models.Max(column_name), samples=models.Count(column_name))
            row["label"] = Metric.TYPE_VALUE_NUMERIC
            q.append(row)
        else:
            raise ValueError(f"Unsupported metric type: {metric.type}")
        rows = q[:100]
        metric_values.update({"metric": metric_name, "service": service})
        for row in rows:
            label = row["label"]
            value = row["value"]
            samples = row["samples"]
            metric_values.update(
                {
                    "value": value or 0,
                    "label": label,
                    "samples_count": samples,
                    "value_raw": value or 0,
                    "value_num": value if isinstance(value, (float, Decimal, int)) else None,
                }
            )
            log.debug(MetricValue.add(**metric_values))

    def process(self, service, data, valid_from, valid_to, *args, **kwargs):
        if service.is_hostgeonode:
            return self.process_host_geonode(service, data, valid_from, valid_to, *args, **kwargs)
        elif service.is_hostgeoserver:
            return self.process_host_geoserver(service, data, valid_from, valid_to, *args, **kwargs)
        else:
            return self.process_requests(service, data, valid_from, valid_to, *args, **kwargs)

    def process_requests(self, service, requests, valid_from, valid_to):
        """
        Processes request list for specific service, generate stats
        """
        interval = service.check_interval
        periods = generate_periods(valid_from, interval, valid_to)
        for pstart, pend in periods:
            requests_batch = requests.filter(created__gte=pstart, created__lt=pend)
            self.process_requests_batch(service, requests_batch, pstart, pend)

    def set_error_values(self, requests, valid_from, valid_to, service=None, resource=None, event_type=None):
        with_errors = requests.exclude(exceptions=None)
        if not with_errors.exists():
            return

        labels = ExceptionEvent.objects.filter(request__in=with_errors).distinct().values_list("error_type", flat=True)
        defaults = {
            "valid_from": valid_from,
            "valid_to": valid_to,
            "resource": resource,
            "event_type": event_type,
            "metric": "response.error.count",
            "samples_count": requests.count(),
            "label": "count",
            "service": service,
        }
        cnt = with_errors.count()
        log.debug(MetricValue.add(value=cnt, value_num=cnt, value_raw=cnt, **defaults))

        defaults["metric"] = "response.error.types"
        for label in labels:
            cnt = with_errors.filter(exceptions__error_type=label).count()

            defaults["label"] = label

            defaults["samples_count"] = cnt
            log.debug(MetricValue.add(value=cnt, value_num=cnt, value_raw=cnt, **defaults))

    def process_requests_batch(self, service, requests, valid_from, valid_to):
        """
        Processes requests information into metric values
        """
        log.debug("Processing batch of %s requests from %s to %s", requests.count(), valid_from, valid_to)
        if not requests.count():
            return
        event_all = EventType.objects.get(name=EventType.EVENT_ALL)
        metric_defaults = {
            "valid_from": valid_from,
            "valid_to": valid_to,
            "event_type": event_all,
            "resource": None,
            "service": service,
        }
        MetricValue.objects.filter(valid_from__gte=valid_from, valid_to__lte=valid_to, service=service).delete()
        requests = requests.filter(service=service)
        resources = self.extract_resources(requests)

        def push_metric_values(srequests, **mdefaults):
            count = srequests.count()
            count_mdefaults = mdefaults.copy()
            count_mdefaults["value"] = count
            count_mdefaults["label"] = "Count"
            count_mdefaults["value_num"] = count
            count_mdefaults["value_raw"] = count
            count_mdefaults["samples_count"] = count

            log.debug(MetricValue.add("request.count", **count_mdefaults))

            paths = srequests.distinct("request_path").values_list("request_path", flat=True)
            for path in paths:
                count = srequests.filter(request_path=path).count()
                count_mdefaults["value"] = count
                count_mdefaults["label"] = path
                count_mdefaults["value_num"] = count
                count_mdefaults["value_raw"] = count
                count_mdefaults["samples_count"] = count

                log.debug(MetricValue.add("request.path", **count_mdefaults))

            for mname, cname in (
                (
                    "request.ip",
                    "client_ip",
                ),
                (
                    "request.users",
                    "user_identifier",
                ),
                ("request.country", "client_country"),
                (
                    "request.city",
                    "client_city",
                ),
                ("request.region", "client_region"),
                (
                    "request.ua",
                    "user_agent",
                ),
                (
                    "request.ua.family",
                    "user_agent_family",
                ),
                (
                    "response.time",
                    "response_time",
                ),
                (
                    "response.size",
                    "response_size",
                ),
                (
                    "response.status",
                    "response_status",
                ),
                (
                    "request.method",
                    "request_method",
                ),
            ):
                # calculate overall stats
                self.set_metric_values(mname, cname, srequests, **mdefaults)

            self.set_error_values(srequests, valid_from, valid_to, service=service, resource=None)

        push_metric_values(requests, **metric_defaults)

        # for each resource we should calculate another set of stats
        for resource, _requests in [
            (
                None,
                requests,
            )
        ] + resources:
            metric_defaults["resource"] = resource
            metric_defaults["event_type"] = event_all
            push_metric_values(_requests, **metric_defaults)

            # for each event type we need separate metrics set
            event_types = self.extract_event_types(_requests)
            for event_type in event_types:
                event_type_requests = _requests.filter(event_type=event_type)
                metric_defaults["event_type"] = event_type
                push_metric_values(event_type_requests, **metric_defaults)

            # combined event types: ows and non-ows
            for evt, rq in self.extract_special_event_types(_requests):
                metric_defaults["event_type"] = evt
                push_metric_values(rq, **metric_defaults)

    def get_metrics_for(
        self,
        metric_name,
        valid_from=None,
        valid_to=None,
        interval=None,
        service=None,
        label=None,
        user=None,
        resource=None,
        event_type=None,
        service_type=None,
        group_by=None,
        resource_type=None,
    ):
        """
        Returns metric data for given metric. Returned dataset contains list of periods and values in that periods
        """
        utc = pytz.utc

        default_interval = False
        now = datetime.utcnow().replace(tzinfo=utc)
        if not interval:
            default_interval = True
            interval = timedelta(seconds=60)
        if not isinstance(interval, timedelta):
            interval = timedelta(seconds=interval)
        valid_from = valid_from or (now - interval)
        valid_to = valid_to or now
        if (not interval or default_interval) and (valid_to - valid_from).total_seconds() > 24 * 3600:
            default_interval = True
            interval = timedelta(seconds=3600)
        if not isinstance(interval, timedelta):
            interval = timedelta(seconds=interval)
        metric = Metric.objects.get(name=metric_name)
        out = {
            "metric": metric.name,
            "input_valid_from": valid_from.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "input_valid_to": valid_to.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "interval": interval.total_seconds(),
            "label": label.name if label else None,
            "type": metric.type,
            "axis_label": metric.unit,
            "data": [],
        }
        periods = generate_periods(valid_from, interval, valid_to, align=False)
        for pstart, pend in periods:
            pdata = self.get_metrics_data(
                metric_name,
                pstart,
                pend,
                interval=interval,
                service=service,
                label=label,
                user=user,
                event_type=event_type,
                service_type=service_type,
                resource=resource,
                resource_type=resource_type,
                group_by=group_by,
            )
            out["data"].append(
                {
                    "valid_from": pstart.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "valid_to": pend.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "data": pdata,
                }
            )
        return out

    def get_aggregate_function(self, column_name, metric_name, service=None):
        """
        Returns string with metric value column name surrounded by aggregate function
        based on metric type (which tells how to interpret value - is it a counter,
        rate or something else).
        """
        metric = Metric.get_for(metric_name, service=service)
        if not metric:
            raise ValueError(f"Invalid metric {metric_name}")
        f = metric.get_aggregate_name()
        return f or column_name

    def get_metrics_data(
        self,
        metric_name,
        valid_from,
        valid_to,
        interval,
        service=None,
        label=None,
        user=None,
        resource=None,
        resource_type=None,
        event_type=None,
        service_type=None,
        group_by=None,
    ):
        """
        Returns metric values for metric within given time span
        """
        utc = pytz.utc
        params = {}
        col = "mv.value_num"
        agg_f = self.get_aggregate_function(col, metric_name, service)
        has_agg = agg_f != col
        group_by_map = {
            "resource": {
                "select": ["mr.id", "mr.type", "mr.name", "mr.resource_id"],
                "from": ["join monitoring_monitoredresource mr on (mv.resource_id = mr.id)"],
                "where": ["and mv.resource_id is not NULL"],
                "order_by": None,
                "grouper": ["resource", "name", "type", "id", "resource_id"],
            },
            # for each resource get the number of unique labels
            "resource_on_label": {
                "select_only": [
                    "mr.id",
                    "mr.type",
                    "mr.name",
                    "mr.resource_id",
                    "count(distinct(ml.name)) as val",
                    "count(1) as metric_count",
                    "sum(samples_count) as samples_count",
                    "sum(mv.value_num), min(mv.value_num)",
                    "max(mv.value_num)",
                ],
                "from": [("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)")],
                "where": ["and mv.resource_id is not NULL"],
                "order_by": ["val desc"],
                "group_by": ["mr.id", "mr.type", "mr.name"],
                "grouper": ["resource", "name", "type", "id", "resource_id"],
            },
            # for each resource get the number of unique users
            "resource_on_user": {
                "select_only": [
                    "mr.id",
                    "mr.type",
                    "mr.name",
                    "mr.resource_id",
                    "count(distinct(ml.user)) as val",
                    "count(1) as metric_count",
                    "sum(samples_count) as samples_count",
                    "sum(mv.value_num), min(mv.value_num)",
                    "max(mv.value_num)",
                ],
                "from": [("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)")],
                "where": ["and mv.resource_id is not NULL"],
                "order_by": ["val desc"],
                "group_by": ["mr.id", "mr.type", "mr.name"],
                "grouper": ["resource", "name", "type", "id", "resource_id"],
            },
            # resource count
            "count_on_resource": {
                "select_only": [
                    (
                        "count(distinct(mr.id)) as val, "
                        "count(1) as metric_count, "
                        "sum(samples_count) as samples_count, "
                        "sum(mv.value_num), min(mv.value_num), "
                        "max(mv.value_num)"
                    )
                ],
                "from": [("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)")],
                "where": ["and mr.id is not NULL"],
                "order_by": ["val desc"],
                "group_by": [],
                "grouper": [],
            },
            "event_type": {
                "select_only": [
                    "ev.name as event_type",
                    "sum(mv.value_num) as val",
                    "count(1) as metric_count",
                    "sum(samples_count) as samples_count",
                    "sum(mv.value_num), min(mv.value_num)",
                    "max(mv.value_num)",
                ],
                "from": [
                    "join monitoring_eventtype ev on (ev.id = mv.event_type_id)",
                    ("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)"),
                ],
                "where": [],
                "order_by": ["val desc"],
                "group_by": ["ev.name"],
                "grouper": [],
            },
            # for each event the unique label count
            "event_type_on_label": {
                "select_only": [
                    "ev.name as event_type",
                    "count(distinct(ml.name)) as val",
                    "count(1) as metric_count",
                    "sum(samples_count) as samples_count",
                    "sum(mv.value_num), min(mv.value_num)",
                    "max(mv.value_num)",
                ],
                "from": [
                    "join monitoring_eventtype ev on (ev.id = mv.event_type_id)",
                    ("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)"),
                ],
                "where": [],
                "order_by": ["val desc"],
                "group_by": ["ev.name"],
                "grouper": [],
            },
            # for each event the unique user count
            "event_type_on_user": {
                "select_only": [
                    "ev.name as event_type",
                    "count(distinct(ml.user)) as val",
                    "count(1) as metric_count",
                    "sum(samples_count) as samples_count",
                    "sum(mv.value_num), min(mv.value_num)",
                    "max(mv.value_num)",
                ],
                "from": [
                    "join monitoring_eventtype ev on (ev.id = mv.event_type_id)",
                    ("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)"),
                ],
                "where": [],
                "order_by": ["val desc"],
                "group_by": ["ev.name"],
                "grouper": [],
            },
            # group by user: number of unique user
            "user": {
                "select_only": [
                    (
                        "count(distinct(ml.user)) as val, "
                        "count(1) as metric_count, sum(samples_count) as samples_count, "
                        "sum(mv.value_num), min(mv.value_num), max(mv.value_num)"
                    )
                ],
                "from": [("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)")],
                # 'from': [], do we want to retrieve also events not related to a monitored resource?
                "where": ["and ml.user is not NULL"],
                "order_by": ["val desc"],
                "group_by": [],
                "grouper": [],
            },
            # number of labels for each user
            "user_on_label": {
                "select_only": [
                    "ml.user as user, count(distinct(ml.name)) as val, " "count(1) as metric_count",
                    "sum(samples_count) as samples_count",
                    "sum(mv.value_num), min(mv.value_num)",
                    "max(mv.value_num)",
                ],
                "from": [("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)")],
                "where": ["and ml.user is not NULL"],
                "order_by": ["val desc"],
                "group_by": ["ml.user"],
                "grouper": [],
            },
            # group by label
            "label": {
                "select_only": [
                    (
                        "count(distinct(ml.name)) as val, "
                        "count(1) as metric_count, sum(samples_count) as samples_count, "
                        "sum(mv.value_num), min(mv.value_num), max(mv.value_num)"
                    )
                ],
                "from": [("join monitoring_monitoredresource mr " "on (mv.resource_id = mr.id)")],
                "where": [],  # ["and mv.resource_id is NULL or (mr.type = '')"],
                "order_by": ["val desc"],
                "group_by": [],
                "grouper": [],
            },
        }

        q_from = [
            "from monitoring_metricvalue mv",
            "join monitoring_servicetypemetric mt on (mv.service_metric_id = mt.id)",
            "join monitoring_metric m on (m.id = mt.metric_id)",
            "join monitoring_metriclabel ml on (mv.label_id = ml.id) ",
        ]
        q_where = [
            "where",
            " ((mv.valid_from >= TIMESTAMP %(valid_from)s AT TIME ZONE 'UTC' ",
            "and mv.valid_to < TIMESTAMP %(valid_to)s AT TIME ZONE 'UTC') ",
            "or (mv.valid_from > TIMESTAMP %(valid_from)s AT TIME ZONE 'UTC' ",
            "and mv.valid_to <= TIMESTAMP %(valid_to)s AT TIME ZONE 'UTC')) ",
            "and m.name = %(metric_name)s",
        ]
        if metric_name == "uptime":
            q_where = ["where", "m.name = %(metric_name)s"]
        q_group = ["ml.name"]

        params.update(
            {
                "metric_name": metric_name,
                "valid_from": valid_from.replace(tzinfo=utc).isoformat(),
                "valid_to": valid_to.replace(tzinfo=utc).isoformat(),
            }
        )

        q_order_by = ["val desc"]

        q_select = [
            (
                f"select ml.name as label, {agg_f} as val, "
                "count(1) as metric_count, sum(samples_count) as samples_count, "
                "sum(mv.value_num), min(mv.value_num), max(mv.value_num)"
            )
        ]
        if service and service_type:
            raise ValueError("Cannot use service and service type in the same query")
        if service:
            q_where.append("and mv.service_id = %(service_id)s")
            params["service_id"] = service.id
        elif service_type:
            q_from.append(
                "join monitoring_service ms on "
                "(ms.id = mv.service_id and ms.service_type_id = %(service_type_id)s ) "
            )
            params["service_type_id"] = service_type.id

        if event_type is None and group_by not in ("event_type", "event_type_on_label", "event_type_on_user"):
            event_type = EventType.get(EventType.EVENT_ALL)

        exclude_ev_type = BuiltIns.host_metrics + ("response.error.count",)

        if event_type and metric_name not in exclude_ev_type:
            q_where.append(" and mv.event_type_id = %(event_type)s ")
            params["event_type"] = event_type.id

        if label:
            q_where.append(" and ml.id = %(label)s")
            params["label"] = label.id
        # if not group_by and not resource:
        #     resource = MonitoredResource.get('', '', or_create=True)

        if resource and has_agg:
            q_group.append("mr.name")
            # group returned columns into a dict
            # config in grouping map: target_column = {source_column1: val, ...}

        if label and has_agg:
            q_group.extend(["ml.name"])

        grouper = None
        if group_by:
            group_by_cfg = group_by_map[group_by]
            g_sel = group_by_cfg.get("select")
            if g_sel:
                q_select.append(f", {(', '.join(g_sel))}")

            g_sel = group_by_cfg.get("select_only")
            if g_sel:
                q_select = [f"select {(', '.join(g_sel))}"]

            q_from.extend(group_by_cfg["from"])
            q_where.extend(group_by_cfg["where"])
            if group_by_cfg.get("group_by") is not None:
                q_group = group_by_cfg["group_by"]
            else:
                q_group.extend(group_by_cfg["select"])
            grouper = group_by_cfg["grouper"]

        if resource_type and not resource:
            if not [mr for mr in q_from if "monitoring_monitoredresource" in mr]:
                q_from.append("join monitoring_monitoredresource mr on mv.resource_id = mr.id ")
            q_where.append(" and mr.type = %(resource_type)s ")
            params["resource_type"] = resource_type

        if resource and group_by in (
            "resource",
            "resource_on_label",
            "resource_on_user",
        ):
            raise ValueError("Cannot use resource and group by resource at the same time")
        elif resource:
            if not [mr for mr in q_from if "monitoring_monitoredresource" in mr]:
                q_from.append("join monitoring_monitoredresource mr on mv.resource_id = mr.id ")
            q_where.append(" and mr.id = %(resource_id)s ")
            params["resource_id"] = resource.id

        if "ml.name" in q_group:
            q_select.append(", max(ml.user) as user")
            # q_group.extend(['ml.user']) not needed

        if user:
            q_where.append(" and ml.user = %(user)s ")
            params["user"] = user

        if q_group:
            q_group = [" group by ", ",".join(q_group)]
        if q_order_by:
            q_order_by = f"order by {(','.join(q_order_by))}"

        q = " ".join(chain(q_select, q_from, q_where, q_group, [q_order_by]))

        def postproc(row):
            if grouper:
                t = {}
                tcol = grouper[0]
                for scol in grouper[1:]:
                    if scol == "resource_id":
                        if scol in row:
                            r_id = row.pop(scol)
                            if "type" in t and t["type"] != MonitoredResource.TYPE_URL:
                                try:
                                    rb = ResourceBase.objects.get(id=r_id)
                                    t["href"] = rb.detail_url
                                except Exception:
                                    t["href"] = ""
                    else:
                        t[scol] = row.pop(scol)
                        if scol == "type" and scol in t and t[scol] == MonitoredResource.TYPE_URL:
                            try:
                                resolve(t["name"])
                                t["href"] = t["name"]
                            except Resolver404:
                                t["href"] = ""
                row[tcol] = t
            return row

        def check_row(r):
            is_ok = True
            # Avoid Count label for countries
            # (it has been already fixed in "set_metric_values"
            # but the following line avoid showing the label in case of existing dirty db)
            if metric_name == "request.country" and r["label"] == "count":
                is_ok = False
            return is_ok

        return [postproc(row) for row in raw_sql(q, params) if check_row(row)]

    def aggregate_past_periods(self, metric_data_q=None, periods=None, **kwargs):
        """
        Aggregate past metric data into longer periods

        """
        return aggregate_past_periods(metric_data_q, periods, **kwargs)

    def clear_old_data(self):
        utc = pytz.utc
        threshold = settings.MONITORING_DATA_TTL
        if not isinstance(threshold, timedelta):
            raise TypeError(
                "MONITORING_DATA_TTL should be an instance of " f"datatime.timedelta, not {threshold.__class__}"
            )
        cutoff = datetime.utcnow().replace(tzinfo=utc) - threshold
        ExceptionEvent.objects.filter(created__lte=cutoff).delete()
        RequestEvent.objects.filter(created__lte=cutoff).delete()
        MetricValue.objects.filter(valid_to__lte=cutoff).delete()

    def compose_notifications(self, ndata, when=None):
        utc = pytz.utc
        return {"alerts": ndata, "when": when or datetime.utcnow().replace(tzinfo=utc), "host": settings.SITEURL}

    def emit_notifications(self, for_timestamp=None):
        notifications = self.get_notifications(for_timestamp)
        for n, ndata in notifications:
            if not n.can_send:
                continue
            try:
                users = n.get_users()
                content = self.compose_notifications(ndata, when=for_timestamp)
                send_notification(users=users, label=AppConf.NOTIFICATION_NAME, extra_context=content)
                emails = n.get_emails()
                self.send_mails(n, emails, ndata, for_timestamp)
            finally:
                n.mark_send()

    def send_mails(self, notification, emails, ndata, when=None):
        base_ctx = self.compose_notifications(ndata, when=when)
        subject = _(f"GeoNode Monitoring on {base_ctx['host']} " f"reports errors: {notification.notification_subject}")
        for email in emails:
            ctx = {"recipient": {"username": email}}
            ctx.update(base_ctx)
            body_html = get_template("pinax/notifications/monitoring_alert/full.txt").render(ctx)
            body_plain = strip_tags(body_html)

            msg = EmailMessage(subject, body_plain, to=(email,))
            msg.attach_alternative(body_html, "text/html")
            msg.send()

    def get_last_usable_timestamp(self):
        metrics = Metric.objects.filter(notification_checks__isnull=False).distinct()
        mv = MetricValue.objects.filter(service_metric__metric__in=metrics).aggregate(Max("valid_to"))
        return mv["valid_to__max"]

    def get_notifications(self, for_timestamp=None):
        if for_timestamp is None:
            for_timestamp = self.get_last_usable_timestamp()
        notifications = NotificationCheck.check_for(for_timestamp=for_timestamp, active=True)
        non_empty = [n for n in notifications if n[1]]
        return non_empty
