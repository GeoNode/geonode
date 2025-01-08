#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from django.contrib import admin
from unfold.admin import ModelAdmin

# Register your models here.

from geonode.monitoring.models import (
    Host,
    Service,
    ServiceType,
    ServiceTypeMetric,
    Metric,
    RequestEvent,
    ExceptionEvent,
    MetricLabel,
    MetricValue,
    MonitoredResource,
    NotificationCheck,
    MetricNotificationCheck,
    NotificationMetricDefinition,
    NotificationReceiver,
    EventType,
)


@admin.register(Host)
class HostAdmin(ModelAdmin):
    list_display = (
        "name",
        "active",
    )


@admin.register(EventType)
class EventTypeAdmin(ModelAdmin):
    list_display = ("name",)


@admin.register(ServiceType)
class ServiceTypeAdmin(ModelAdmin):
    list_display = ("name",)


@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = (
        "name",
        "active",
        "host_name",
        "service_type",
        "last_check",
        "url",
    )

    def host_name(self, obj):
        return obj.host.name

    def service_type(self, obj):
        return obj.service_type.name

    list_select_related = True


@admin.register(ServiceTypeMetric)
class ServiceTypeMetricAdmin(ModelAdmin):
    list_display = (
        "service_type",
        "metric",
    )
    list_select_related = True
    list_filter = (
        "service_type",
        "metric",
    )


@admin.register(Metric)
class MetricAdmin(ModelAdmin):
    list_display = (
        "name",
        "type",
    )
    list_filter = ("type",)


@admin.register(RequestEvent)
class RequestEvent(ModelAdmin):
    list_display = (
        "service",
        "created",
        "received",
        "request_method",
        "response_status",
        "event_type",
        "response_size",
        "client_country",
        "request_path",
    )
    list_filter = (
        "host",
        "service",
        "request_method",
        "response_status",
        "event_type",
    )


@admin.register(MetricLabel)
class MetricLabelAdmin(ModelAdmin):
    list_display = ("name",)


@admin.register(MetricValue)
class MetricValueAdmin(ModelAdmin):
    list_display = (
        "service_metric",
        "service",
        "event_type",
        "resource",
        "label",
        "value",
        "value_num",
        "value_raw",
        "samples_count",
        "data",
    )
    list_filter = ("service_metric", "service", "event_type")


@admin.register(MonitoredResource)
class MonitoredResourceAdmin(ModelAdmin):
    list_display = (
        "id",
        "name",
        "type",
    )
    list_filter = ("type",)


@admin.register(ExceptionEvent)
class ExceptionEventAdmin(ModelAdmin):
    list_display = (
        "created",
        "service",
        "error_type",
    )


@admin.register(NotificationCheck)
class NotificationCheckAdmin(ModelAdmin):
    list_display = (
        "name",
        "active",
    )
    list_filter = ("active",)


@admin.register(MetricNotificationCheck)
class MetricNotificationCheckAdmin(ModelAdmin):
    list_display = (
        "id",
        "notification_check",
        "metric",
        "min_value",
        "max_value",
        "max_timeout",
    )
    raw_id_fields = (
        "notification_check",
        "resource",
        "label",
    )


@admin.register(NotificationMetricDefinition)
class NotificationCheckDefinitionAdmin(ModelAdmin):
    list_display = (
        "notification_check",
        "metric",
        "field_option",
        "min_value",
        "max_value",
        "steps",
    )
    raw_id_fields = (
        "notification_check",
        "metric",
    )


@admin.register(NotificationReceiver)
class NotificationReceiverAdmin(ModelAdmin):
    list_display = (
        "notification_check",
        "user",
        "email",
    )
    raw_id_fields = (
        "notification_check",
        "user",
    )
