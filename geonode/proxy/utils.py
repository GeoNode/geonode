from threading import RLock
from urllib.parse import urlsplit

from django.conf import settings
from django.utils.timezone import now

site_url = urlsplit(settings.SITEURL)

PROXIED_LINK_TYPES = ["OGC:WMS", "OGC:WFS", "data"]


class ProxyUrlsRegistry:
    _registry_reload_threshold = getattr(settings, "PROXY_RELOAD_REGISTRY_THRESHOLD_DAYS", 1)

    def __init__(self):
        self._lock = RLock()
        self._last_registry_load = None
        self._proxy_allowed_hosts = None

    def _needs_initialization(self):
        return (
            self._last_registry_load is None
            or (now() - self._last_registry_load).days >= self._registry_reload_threshold
        )

    @property
    def proxy_allowed_hosts(self):
        # We register remote hosts from remote URLs at creation time, inside ImporterViewSet.create().
        # If for some reason the creation fails we end up having stale or wrong URLs inside the registry.
        # We check the last time the registry was updated, and after a certain delta we reinitialize the registry
        # which removes any URLs that are not connected to remote datasets.
        if self._needs_initialization():
            with self._lock:
                if self._needs_initialization():
                    self._initialize()
        return self._proxy_allowed_hosts

    @proxy_allowed_hosts.setter
    def proxy_allowed_hosts(self, hosts):
        self._proxy_allowed_hosts = set(hosts)

    def _initialize(self):
        from geonode.base.models import Link
        from geonode.geoserver.helpers import ogc_server_settings

        proxy_allowed_hosts = set([site_url.hostname] + list(getattr(settings, "PROXY_ALLOWED_HOSTS", ())))

        if ogc_server_settings:
            proxy_allowed_hosts.add(ogc_server_settings.hostname)

        for link in Link.objects.filter(resource__sourcetype="REMOTE", link_type__in=PROXIED_LINK_TYPES):
            remote_host = urlsplit(link.url).hostname
            proxy_allowed_hosts.add(remote_host)

        self.proxy_allowed_hosts = proxy_allowed_hosts
        self._last_registry_load = now()

    def initialize(self):
        """Rebuild the registry safely for direct callers."""
        with self._lock:
            self._initialize()

    def set(self, hosts):
        with self._lock:
            self.proxy_allowed_hosts = set(hosts)
            self._last_registry_load = now()
        return self

    def clear(self):
        with self._lock:
            self.proxy_allowed_hosts = set()
            self._last_registry_load = now()
        return self

    def register_host(self, host):
        with self._lock:
            self.proxy_allowed_hosts.add(host)

    def unregister_host(self, host):
        with self._lock:
            self.proxy_allowed_hosts.remove(host)

    def get_proxy_allowed_hosts(self):
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
