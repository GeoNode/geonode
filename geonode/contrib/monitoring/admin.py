from django.contrib import admin

# Register your models here.

from geonode.contrib.monitoring.models import (
    Host,
    Service,
    ServiceType,
    ServiceTypeMetric,
    Metric,
    RequestEvent,
    ExceptionEvent,
    MetricLabel,
    MonitoredResource,
    NotificationCheck,
    MetricNotificationCheck,
    NotificationMetricDefinition,
    NotificationReceiver,
    OWSService,)


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'active',)


@admin.register(OWSService)
class OWSServiceAdmin(admin.ModelAdmin):
    list_display = ('name', )


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'host_name', 'service_type', 'last_check', 'url',)

    def host_name(self, obj):
        return obj.host.name

    def service_type(self, obj):
        return obj.service_type.name

    list_select_related = True


@admin.register(ServiceTypeMetric)
class ServiceTypeMetricAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'metric',)
    list_select_related = True
    list_filter = ('service_type', 'metric',)


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'type',)
    list_filter = ('type',)


@admin.register(RequestEvent)
class RequestEvent(admin.ModelAdmin):
    list_display = ('service', 'created', 'received', 'request_method', 'response_status',
                    'ows_service', 'response_size', 'client_country', 'request_path')
    list_filter = ('host', 'service', 'request_method', 'response_status', 'ows_service',)


@admin.register(MetricLabel)
class MetricLabelAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(MonitoredResource)
class MonitoredResourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type',)
    list_filter = ('type',)


@admin.register(ExceptionEvent)
class ExceptionEventAdmin(admin.ModelAdmin):
    list_display = ('created', 'service', 'error_type',)


@admin.register(NotificationCheck)
class NotificationCheckAdmin(admin.ModelAdmin):
    list_display = ('name', 'active',)
    list_filter = ('active',)


@admin.register(MetricNotificationCheck)
class MetricNotificationCheckAdmin(admin.ModelAdmin):
    list_display = ('id', 'notification_check', 'metric', 'min_value', 'max_value', 'max_timeout',)
    raw_id_fields = ('notification_check', 'resource', 'label',)


@admin.register(NotificationMetricDefinition)
class NotificationCheckDefinitionAdmin(admin.ModelAdmin):
    list_display = ('notification_check', 'metric', 'field_option', 'min_value', 'max_value', 'steps',)
    raw_id_fields = ('notification_check', 'metric',)


@admin.register(NotificationReceiver)
class NotificationReceiverAdmin(admin.ModelAdmin):
    list_display = ('notification_check', 'user', 'email',)
    raw_id_fields = ('notification_check', 'user',)
