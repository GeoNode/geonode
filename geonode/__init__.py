import os
__version__ = (1, 2, 0, 'alpha', 0)


class GeoNodeException(Exception):
    """Base class for exceptions in this module."""
    pass


def get_version():
    import geonode.version
    return geonode.version.get_version(__version__)


def main(global_settings, **settings):
    from django.core.wsgi import get_wsgi_application
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings.get('django_settings'))
    app = get_wsgi_application()
    return app
