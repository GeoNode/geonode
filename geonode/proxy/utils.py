from urllib.parse import urlsplit

from django.conf import settings
from django.db.models import signals

from geonode.base.models import Link
from geonode.services.models import Service

site_url = urlsplit(settings.SITEURL)

PROXIED_LINK_EXTENSIONS = ["3dtiles"]

class ProxyUrlsRegistry:
    
    def initialize(self):
        from geonode.geoserver.helpers import ogc_server_settings
  
        self.proxy_allowed_hosts = set([site_url.hostname] + list(getattr(settings, "PROXY_ALLOWED_HOSTS", ())))

        if ogc_server_settings:
            self.proxy_allowed_hosts.add(ogc_server_settings.hostname)

        for _s in Service.objects.all():
            _remote_host = urlsplit(_s.base_url).hostname
            self.proxy_allowed_hosts.add(_remote_host)

    def set(self, hosts):
        self.proxy_allowed_hosts = set(hosts)
        return self

    def clear(self):
        self.proxy_allowed_hosts = set()
        return self

    def register_host(self, host):
        self.proxy_allowed_hosts.add(host)

    def unregister_host(self, host):
        self.proxy_allowed_hosts.remove(host)

    def get_proxy_allowed_hosts(self):
        return self.proxy_allowed_hosts


proxy_urls_registry = ProxyUrlsRegistry()


def service_post_save(instance, sender, **kwargs):
    service_hostname = urlsplit(instance.base_url).hostname
    proxy_urls_registry.register_host(service_hostname)


def service_post_delete(instance, sender, **kwargs):
    # We reinitialize the registry otherwise we might delete a host requested by another service with the same hostanme
    proxy_urls_registry.initialize()

signals.post_save.connect(service_post_save, sender=Service)
signals.post_delete.connect(service_post_delete, sender=Service)
'''
from geonode.base.models import Link


def link_post_save(instance, sender, **kwargs):
    if (
        instance.resource
        and instance.resource.sourcetype == "REMOTE"
        and instance.url
        and instance.extension in PROXIED_LINK_EXTENSIONS
    ):
        service_hostname = urlsplit(instance.url).hostname
        proxy_urls_registry.register_host(service_hostname)


def link_post_delete(instance, sender, **kwargs):
    # We reinitialize the registry otherwise we might delete a host requested by another service with the same hostanme
    proxy_urls_registry.initialize()




signals.post_save.connect(link_post_save, sender=Link)
signals.post_delete.connect(link_post_delete, sender=Link)
'''