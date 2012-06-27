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
    settings.GEONODE_CSW = { DEFAULT_CSW_ALIAS: 'geonode.backends.dummy'}

# If settings.GEONODE_CSW is defined, we expect it to be properly named
if DEFAULT_CSW_ALIAS not in settings.GEONODE_CSW:
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


def default_csw_backend():
    """Get the default bakcend
    """
    return settings.GEONODE_CSW[DEFAULT_CSW_ALIAS]


def get_catalogue(backend=None):
    """Returns a catalogue object.
    """
    default_backend_config = backend or default_csw_backend()
    backend_name = default_backend_config['ENGINE']
    catalog_module = load_backend(backend_name)
    assert hasattr(catalog_module, 'CSWBackend'), '%s must define a CSWBackend class'
    catalog_class = catalog_module.CSWBackend
    cat = catalog_class(**default_backend_config)
    return cat


def get_record(uuid):
    with CSW() as csw_cat:
        rec = csw_cat.get_by_uuid(uuid)
        rec.links = {}
        rec.links['metadata'] = csw_cat.urls_for_uuid(uuid)
        rec.links['download'] = csw_cat.extract_links(rec)
    return rec

def search(keywords, start, limit, bbox):
  with CSW() as csw_cat: 
        bbox = csw_cat.normalize_bbox(kw['bbox'])
        csw_cat.search(keywords, start+1, limit, bbox)

        # build results into JSON for API
        results = [csw_cat.metadatarecord2dict(doc) for v, doc in csw_cat.records.iteritems()]

        result = {
                  'rows': results,
                  'total': csw_cat.results['matches'],
                  'next_page': csw_cat.results.get('nextrecord', 0)
                  }

        return result


def remove_record(uuid):
    with CSW() as csw_cat:
       catalogue_record = csw_cat.get_by_uuid(uuid)
       if catalogue_record is None:
           return

       try:
           # this is a bit hacky, delete_layer expects an instance of the layer
           # model but it just passes it to a Django template so a dict works
           # too.
           csw_cat.delete_layer({ "uuid": uuid })
       except:
           logger.exception('Couldn\'t delete Catalogue record '
                                'during cleanup()')

def create_record(item):
    with CSW() as csw_cat:
        record = csw_cat.get_by_uuid(item.uuid)
        if record is None:
            md_link = csw_cat.create_from_layer(item)
            self.metadata_links = [("text/xml", "TC211", md_link)]
        else:
            csw_cat.update_layer(item)

class CSW(object):

    def __init__(self, *args, **kwargs):
        self.csw_cat = get_catalogue()

    def __enter__(self, *args, **kwargs):
        self.csw_cat.login()
        return self.csw_cat

    def __exit__(self, *args, **kwargs):
        self.csw_cat.logout()
