from urllib.parse import urlsplit

from django.conf import settings


site_url = urlsplit(settings.SITEURL)


class ProxyUrlsRegistry:
    def initialize(self):
        from geonode.geoserver.helpers import ogc_server_settings
        from geonode.services.models import Service

        self.proxy_alloed_hosts = set()

        self.proxy_alloed_hosts.add(site_url.hostname)

        hostname = ogc_server_settings.hostname if ogc_server_settings else None
        if hostname:
            self.proxy_alloed_hosts.add(hostname)

        for _s in Service.objects.all():
            _remote_host = urlsplit(_s.base_url).hostname
            self.proxy_alloed_hosts.add(_remote_host)

    def set(self, hosts):
        self.proxy_alloed_hosts = set(hosts)
        return self

    def clear(self):
        self.proxy_alloed_hosts = set()
        return self

    def register_host(self, host):
        self.proxy_alloed_hosts.add(host)

    def unregister_host(self, host):
        self.proxy_alloed_hosts.remove(host)

    def get_proxy_alloed_hosts(self):
        return self.proxy_alloed_hosts


proxy_urls_registry = ProxyUrlsRegistry()
