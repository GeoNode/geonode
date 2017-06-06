from django.contrib import admin

# Register your models here.

from geonode.contrib.monitoring.models import Host, Service, ServiceType, ServiceTypeMetric, Metric, RequestEvent, ExceptionEvent 


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'active',)


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'host_name', 'service_type',)

    def host_name(self, obj):
        return obj.host.name

    def service_type(self, obj):
        return obj.service_type.name

    list_select_related = True

@admin.register(ServiceTypeMetric)
class ServiceTypeMetricAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'metric',)
    list_select_related = True


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(RequestEvent)
class RequestEvent(admin.ModelAdmin):
    list_display = ('host', 'request_method', 'request_path', 'response_status',)
    list_filter = ('host', 'request_method', 'response_status', 'ows_type',)
