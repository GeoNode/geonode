"""
Tools for managing a CatalogWebService (CSW)
"""
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from contextlib import contextmanager


DEFAULT_CSW_ALIAS = 'default'

# GeoNode uses this if the CSW setting is empty (None).
if not hasattr(settings, 'CSW'):
    settings.CSW = { DEFAULT_CSW_ALIAS: 'geonode.backends.dummy'}

# If settings.CSW is defined, we expect it to be properly named
if DEFAULT_CSW_ALIAS not in settings.CSW:
    raise ImproperlyConfigured("You must define a '%s' CSW" % DEFAULT_CSW_ALIAS)


def load_backend(backend_name):
    # Look for a fully qualified CSW backend name
    try:
        return import_module(backend_name)
    except ImportError as e_user:
        # The CSW backend wasn't found. Display a helpful error message
        # listing all possible (built-in) CSW backends.
        backend_dir = os.path.join(os.path.dirname(__file__), 'backends')
        try:
            available_backends = [f for f in os.listdir(backend_dir)
                    if os.path.isdir(os.path.join(backend_dir, f))
                    and not f.startswith('.')]
        except EnvironmentError:
            available_backends = []

        if backend_name not in available_backends:
            backend_reprs = map(repr, sorted(available_backends))
            error_msg = ("%r isn't an available catalogue backend.\n"
                         "Try using geonode.catalogue.backends.XXX, where XXX "
                         "is one of:\n    %s\nError was: %s" %
                         (backend_name, ", ".join(backend_reprs), e_user))
            raise ImproperlyConfigured(error_msg)
        else:
            # If there's some other error, this must be an error in GeoNode
            raise


def get_catalogue(backend=None):
    """Returns a catalogue object.
    """
    the_backend = backend or settings.CSW
    default_backend_config = the_backend[DEFAULT_CSW_ALIAS]
    backend_name = default_backend_config['ENGINE']
    catalog_module = load_backend(backend_name)
    assert hasattr(catalog_module, 'CSWBackend'), '%s must define a CSWBackend class'
    catalog_class = catalog_module.CSWBackend
    cat = catalog_class(**default_backend_config)
    return cat


class CSW(object):

    def __init__(self, *args, **kwargs):
        self.csw_cat = get_catalogue()

    def __enter__(self, *args, **kwargs):
        self.csw_cat.login()
        return self.csw_cat

    def __exit__(self, *args, **kwargs):
        self.csw_cat.logout()
