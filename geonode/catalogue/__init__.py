#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

"""
Tools for managing a Catalogue Service for the Web (CSW)
"""
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from importlib import import_module

DEFAULT_CATALOGUE_ALIAS = 'default'

# GeoNode uses this if the CATALOGUE setting is empty (None).
if not hasattr(settings, 'CATALOGUE'):
    settings.CATALOGUE = {DEFAULT_CATALOGUE_ALIAS: 'geonode.backends.dummy'}

# If settings.CATALOGUE is defined, we expect it to be properly named
if DEFAULT_CATALOGUE_ALIAS not in settings.CATALOGUE:
    raise ImproperlyConfigured(f"You must define a '{DEFAULT_CATALOGUE_ALIAS}' CATALOGUE")


def load_backend(backend_name):
    """load a Catalogue backend"""
    # Look for a fully qualified CSW backend name
    try:
        return import_module(backend_name)
    except ImportError as e_user:
        # The CSW backend wasn't found. Display a helpful error message
        # listing all possible (built-in) CSW backends.
        backend_dir = os.path.join(os.path.dirname(__file__), 'backends')
        try:
            available_backends = sorted([f for f in os.listdir(backend_dir) if os.path.isdir(os.path.join(backend_dir, f)) and
                                         not f.startswith('.')])
        except OSError:
            available_backends = []

        if backend_name not in available_backends:
            backend_reprs = list(map(repr, available_backends))
            error_msg = (f"{backend_name!r} isn't an available catalogue backend.\n"
                         "Try using geonode.catalogue.backends.BACKEND, where BACKEND is one of:\n"
                         f"    {', '.join(backend_reprs)}\nError was: {e_user}")
            raise ImproperlyConfigured(error_msg)
        else:
            # If there's some other error, this must be an error in GeoNode
            raise


def default_catalogue_backend():
    """Get the default backend
    """
    msg = f"There is no '{DEFAULT_CATALOGUE_ALIAS}' backend in CATALOGUE"
    assert DEFAULT_CATALOGUE_ALIAS in settings.CATALOGUE, msg
    return settings.CATALOGUE[DEFAULT_CATALOGUE_ALIAS]


def get_catalogue(backend=None, skip_caps=True):
    """Returns a catalogue object.
    """
    default_backend_config = backend or default_catalogue_backend()
    backend_name = default_backend_config['ENGINE']
    catalog_module = load_backend(backend_name)
    assert hasattr(catalog_module, 'CatalogueBackend'), \
        '%s must define a CatalogueBackend class'
    catalog_class = catalog_module.CatalogueBackend
    cat = catalog_class(skip_caps=skip_caps, **default_backend_config)
    return cat
