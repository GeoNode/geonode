from urllib.parse import urlsplit

from django.conf import settings
from django.db.models import signals
from django.utils.timezone import now

site_url = urlsplit(settings.SITEURL)

PROXIED_LINK_TYPES = ["OGC:WMS", "OGC:WFS", "data"]


class ProxyUrlsRegistry:
    _first_init = True
    _last_registry_load = None
    _registry_reload_threshold = getattr(settings, "PROXY_RELOAD_REGISTRY_THRESHOLD_DAYS", 1)

    def initialize(self):
        from geonode.base.models import Link
        from geonode.geoserver.helpers import ogc_server_settings

        self.proxy_allowed_hosts = set([site_url.hostname] + list(getattr(settings, "PROXY_ALLOWED_HOSTS", ())))

        if ogc_server_settings:
            self.register_host(ogc_server_settings.hostname)

        for link in Link.objects.filter(resource__sourcetype="REMOTE", link_type__in=PROXIED_LINK_TYPES):
            remote_host = urlsplit(link.url).hostname
            self.register_host(remote_host)

        if self._first_init:
            signals.post_save.connect(link_post_save, sender=Link)
            signals.post_delete.connect(link_post_delete, sender=Link)
            self._first_init = False

        self._last_registry_load = now()

    def set(self, hosts):
        self.proxy_allowed_hosts = set(hosts)
        self._last_registry_load = now()
        return self

    def clear(self):
        self.proxy_allowed_hosts = set()
        self._last_registry_load = now()
        return self

    def register_host(self, host):
        self.proxy_allowed_hosts.add(host)

    def unregister_host(self, host):
        self.proxy_allowed_hosts.remove(host)

    def get_proxy_allowed_hosts(self):
        if (
            self._last_registry_load is None
            or (now() - self._last_registry_load).days >= self._registry_reload_threshold
        ):
            self.initialize()
        return self.proxy_allowed_hosts


proxy_urls_registry = ProxyUrlsRegistry()


def link_post_save(instance, sender, **kwargs):
    if (
        instance.resource
        and instance.resource.sourcetype == "REMOTE"
        and instance.url
        and instance.link_type in PROXIED_LINK_TYPES
    ):
        remote_host = urlsplit(instance.url).hostname
        proxy_urls_registry.register_host(remote_host)


def link_post_delete(instance, sender, **kwargs):
    # We reinitialize the registry otherwise we might delete a host requested by another service with the same hostanme
    proxy_urls_registry.initialize()
