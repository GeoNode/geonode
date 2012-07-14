"""
Tools for managing a CatalogWebService (CSW)
"""
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from contextlib import contextmanager


DEFAULT_CATALOGUE_ALIAS = 'default'

# GeoNode uses this if the CATALOGUE setting is empty (None).
if not hasattr(settings, 'CATALOGUE'):
    settings.CATALOGUE = { DEFAULT_CSW_ALIAS: 'geonode.backends.dummy'}

# If settings.CATALOGUE is defined, we expect it to be properly named
if DEFAULT_CATALOGUE_ALIAS not in settings.CATALOGUE:
    raise ImproperlyConfigured("You must define a '%s' CATALOGUE" % DEFAULT_CATALOGUE_ALIAS)


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


def default_catalogue_backend():
    """Get the default bakcend
    """
    msg = "There is no '%s' backend in CATALOGUE" % DEFAULT_CATALOGUE_ALIAS
    assert DEFAULT_CATALOGUE_ALIAS in settings.CATALOGUE, msg
    return settings.CATALOGUE[DEFAULT_CATALOGUE_ALIAS]


def get_catalogue(backend=None):
    """Returns a catalogue object.
    """
    default_backend_config = backend or default_catalogue_backend()
    backend_name = default_backend_config['ENGINE']
    catalog_module = load_backend(backend_name)
    assert hasattr(catalog_module, 'CatalogueBackend'), '%s must define a CatalogueBackend class'
    catalog_class = catalog_module.CatalogueBackend
    cat = catalog_class(**default_backend_config)
    return cat


def get_record(uuid):
    with Catalogue() as catalogue:
        rec = catalogue.get_by_uuid(uuid)
        if rec is not None:
            rec.links = {}
            rec.links['metadata'] = catalogue.urls_for_uuid(uuid)
            rec.links['download'] = catalogue.extract_links(rec)
    return rec

def search_records(keywords, start, limit, bbox):
  with Catalogue() as catalogue: 
        bbox = catalogue.normalize_bbox(bbox)
        catalogue.search(keywords, start+1, limit, bbox)

        # build results into JSON for API
        results = [catalogue.metadatarecord2dict(doc) for v, doc in catalogue.records.iteritems()]

        result = {
                  'rows': results,
                  'total': catalogue.results['matches'],
                  'next_page': catalogue.results.get('nextrecord', 0)
                  }

        return result


def remove_record(uuid):
    with Catalogue() as catalogue:
       catalogue_record = catalogue.get_by_uuid(uuid)
       if catalogue_record is None:
           return

       try:
           # this is a bit hacky, delete_layer expects an instance of the layer
           # model but it just passes it to a Django template so a dict works
           # too.
           catalogue.delete_layer({ "uuid": uuid })
       except:
           logger.exception('Couldn\'t delete Catalogue record '
                                'during cleanup()')

def create_record(item):
    with Catalogue() as catalogue:
        record = catalogue.get_by_uuid(item.uuid)
        if record is None:
            md_link = catalogue.create_from_layer(item)
            item.metadata_links = [("text/xml", "TC211", md_link)]
        else:
            catalogue.update_layer(item)

class Catalogue(object):

    def __init__(self, *args, **kwargs):
        self.catalogue = get_catalogue()

    def __enter__(self, *args, **kwargs):
        self.catalogue.login()
        return self.catalogue

    def __exit__(self, *args, **kwargs):
        self.catalogue.logout()
