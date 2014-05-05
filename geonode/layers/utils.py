# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

"""Utilities for managing GeoNode layers
"""

# Standard Modules
import logging
import re
import uuid
import os
import glob
import sys

# Django functionality
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.core.files import File
from django.conf import settings

# Geonode functionality
from geonode import GeoNodeException
from geonode.people.utils import get_valid_user
from geonode.layers.models import Layer, Style, LayerFile, UploadSession
from geonode.people.models import Profile
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.base.models import SpatialRepresentationType, TopicCategory
from geonode.upload.files import _clean_string, _rename_zip

from zipfile import ZipFile

logger = logging.getLogger('geonode.layers.utils')

_separator = '\n' + ('-' * 100) + '\n'

shp_exts = ['.shp',]
csv_exts = ['.csv']
kml_exts = ['.kml']
vec_exts = shp_exts + csv_exts + kml_exts

cov_exts = ['.tif', '.tiff', '.geotiff', '.geotif']



def get_files(filename):
    """Converts the data to Shapefiles or Geotiffs and returns
       a dictionary with all the required files
    """
    files = {}

    # Verify if the filename is in ascii format.
    try:
        filename.decode('ascii')
    except UnicodeEncodeError:
        msg = "Please use only characters from the english alphabet for the filename. '%s' is not yet supported." % os.path.basename(filename).encode('UTF-8')
        raise GeoNodeException(msg)

    # Make sure the file exists.
    if not os.path.exists(filename):
        msg = ('Could not open %s. Make sure you are using a '
               'valid file' % filename)
        logger.warn(msg)
        raise GeoNodeException(msg)

    base_name, extension = os.path.splitext(filename)
    #Replace special characters in filenames - []{}()
    glob_name = re.sub(r'([\[\]\(\)\{\}])', r'[\g<1>]', base_name)

    if extension.lower() == '.shp':
        required_extensions = dict(
            shp='.[sS][hH][pP]', dbf='.[dD][bB][fF]', shx='.[sS][hH][xX]')
        for ext, pattern in required_extensions.iteritems():
            matches = glob.glob(glob_name + pattern)
            if len(matches) == 0:
                msg = ('Expected helper file %s does not exist; a Shapefile '
                       'requires helper files with the following extensions: '
                       '%s') % (base_name + "." + ext,
                                required_extensions.keys())
                raise GeoNodeException(msg)
            elif len(matches) > 1:
                msg = ('Multiple helper files for %s exist; they need to be '
                       'distinct by spelling and not just case.') % filename
                raise GeoNodeException(msg)
            else:
                files[ext] = matches[0]

        matches = glob.glob(glob_name + ".[pP][rR][jJ]")
        if len(matches) == 1:
            files['prj'] = matches[0]
        elif len(matches) > 1:
            msg = ('Multiple helper files for %s exist; they need to be '
                   'distinct by spelling and not just case.') % filename
            raise GeoNodeException(msg)

    elif extension.lower() in cov_exts:
        files[extension.lower().replace('.','')] = filename

    matches = glob.glob(glob_name + ".[sS][lL][dD]")
    if len(matches) == 1:
        files['sld'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple style files for %s exist; they need to be '
               'distinct by spelling and not just case.') % filename
        raise GeoNodeException(msg)

    matches = glob.glob(base_name + ".[xX][mM][lL]")

    # shapefile XML metadata is sometimes named base_name.shp.xml
    # try looking for filename.xml if base_name.xml does not exist
    if len(matches) == 0:
        matches = glob.glob(filename + ".[xX][mM][lL]")

    if len(matches) == 1:
        files['xml'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple XML files for %s exist; they need to be '
               'distinct by spelling and not just case.') % filename
        raise GeoNodeException(msg)

    return files


def layer_type(filename):
    """Finds out if a filename is a Feature or a Vector
       returns a gsconfig resource_type string
       that can be either 'featureType' or 'coverage'
    """
    base_name, extension = os.path.splitext(filename)

    if extension.lower() == '.zip':
        zf = ZipFile(filename)
        # ZipFile doesn't support with statement in 2.6, so don't do it
        try:
            for n in zf.namelist():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    base_name, extension = b,e
        finally:
            zf.close()

    if extension.lower() in vec_exts:
         return 'vector'
    elif extension.lower() in cov_exts:
         return 'raster'
    else:
        msg = ('Saving of extension [%s] is not implemented' % extension)
        raise GeoNodeException(msg)


def get_valid_name(layer_name):
    """
    Create a brand new name
    """

    name = _clean_string(layer_name)
    proposed_name = name
    count = 1
    while Layer.objects.filter(name=proposed_name).count() > 0:
        proposed_name = "%s_%d" % (name, count)
        count = count + 1
        logger.info('Requested name already used; adjusting name '
                    '[%s] => [%s]', layer_name, proposed_name)
    else:
        logger.info("Using name as requested")

    return proposed_name


def get_valid_layer_name(layer, overwrite):
    """Checks if the layer is a string and fetches it from the database.
    """
    # The first thing we do is get the layer name string
    if isinstance(layer, Layer):
        layer_name = layer.name
    elif isinstance(layer, basestring):
        layer_name = layer
    else:
        msg = ('You must pass either a filename or a GeoNode layer object')
        raise GeoNodeException(msg)

    if overwrite:
        return layer_name
    else:
        return get_valid_name(layer_name)


def get_default_user():
    """Create a default user
    """
    superusers = User.objects.filter(is_superuser=True).order_by('id')
    if superusers.count() > 0:
        # Return the first created superuser
        return superusers[0]
    else:
        raise GeoNodeException('You must have an admin account configured '
                               'before importing data. '
                               'Try: django-admin.py createsuperuser')


def file_upload(filename, name=None, user=None, title=None, abstract=None,
                skip=True, overwrite=False, keywords=(), charset='UTF-8'):
    """Saves a layer in GeoNode asking as little information as possible.
       Only filename is required, user and title are optional.
    """
    # Get a valid user
    theuser = get_valid_user(user)

    # Create a new upload session
    upload_session = UploadSession.objects.create(user=theuser)

    # Get all the files uploaded with the layer
    files = get_files(filename)

    # Add them to the upload session (new file fields are created).
    for type_name, filename in files.items():
        f = open(filename)
        us = upload_session.layerfile_set.create(name=type_name,
                                                file=File(f),
                                                )

    # Set a default title that looks nice ...
    if title is None:
        basename = os.path.splitext(os.path.basename(filename))[0]
        title = basename.title().replace('_', ' ')

    # Create a name from the title if it is not passed.
    if name is None:
        name = slugify(title).replace('-', '_')

    # Generate a name that is not taken if overwrite is False.
    valid_name = get_valid_layer_name(name, overwrite)

    # Get or create a layer object and attach the uploaded files.
    layer, created = Layer.objects.get_or_create(name=valid_name,
                                        defaults={
                                            'title': title,
                                            'abstract': abstract,
                                            'owner': user,
                                            'charset': charset,
                                           })

    # Delete the old layers if overwrite is true
    # and the layer was not just created
    if not created and overwrite:
        layer.layerfile_set.all().delete()

    # Assign the uploaded files to this layer.
    upload_session.layerfile_set.all().update(layer=layer)

    # Assign the keywords (needs to be done after saving)
    layer.keywords.add(*keywords)

    # Now that files are in place, save again to trigger all kind of signals.
    layer.save()

    return layer

def upload(incoming, user=None, overwrite=False,
           keywords=(), skip=True, ignore_errors=True,
           verbosity=1, console=None):
    """Upload a directory of spatial data files to GeoNode

       This function also verifies that each layer is in GeoServer.

       Supported extensions are: .shp, .tif, and .zip (of a shapefile).
       It catches GeoNodeExceptions and gives a report per file
    """
    if verbosity > 1:
        print >> console, "Verifying that GeoNode is running ..."

    if console is None:
        console = open(os.devnull, 'w')

    potential_files = []
    if os.path.isfile(incoming):
        ___, short_filename = os.path.split(incoming)
        basename, extension = os.path.splitext(short_filename)
        filename = incoming

        if extension in ['.tif', '.shp', '.zip']:
            potential_files.append((basename, filename))

    elif not os.path.isdir(incoming):
        msg = ('Please pass a filename or a directory name as the "incoming" '
               'parameter, instead of %s: %s' % (incoming, type(incoming)))
        logger.exception(msg)
        raise GeoNodeException(msg)
    else:
        datadir = incoming
        for root, dirs, files in os.walk(datadir):
            for short_filename in files:
                basename, extension = os.path.splitext(short_filename)
                filename = os.path.join(root, short_filename)
                if extension in ['.tif', '.shp', '.zip']:
                    potential_files.append((basename, filename))

    # After gathering the list of potential files,
    # let's process them one by one.
    number = len(potential_files)
    if verbosity > 1:
        msg = "Found %d potential layers." % number
        print >> console, msg

    output = []
    for i, file_pair in enumerate(potential_files):
        basename, filename = file_pair

        existing_layers = Layer.objects.filter(name=basename)

        if existing_layers.count() > 0:
            existed = True
        else:
            existed = False

        if existed and skip:
            save_it = False
            status = 'skipped'
            layer = existing_layers[0]
            if verbosity > 0:
                msg = ('Stopping process because '
                       '--overwrite was not set '
                       'and a layer with this name already exists.')
                print >> sys.stderr, msg
        else:
            save_it = True

        if save_it:
            try:
                layer = file_upload(filename,
                                    user=user,
                                    overwrite=overwrite,
                                    keywords=keywords,
                                    )
                if not existed:
                    status = 'created'
                else:
                    status = 'updated'
            except Exception, e:
                if ignore_errors:
                    status = 'failed'
                    exception_type, error, traceback = sys.exc_info()
                else:
                    if verbosity > 0:
                        msg = ('Stopping process because '
                               '--ignore-errors was not set '
                               'and an error was found.')
                        print >> sys.stderr, msg
                        msg = 'Failed to process %s' % filename
                        raise Exception(msg, e), None, sys.exc_info()[2]

        msg = "[%s] Layer for '%s' (%d/%d)" % (status, filename, i + 1, number)
        info = {'file': filename, 'status': status}
        if status == 'failed':
            info['traceback'] = traceback
            info['exception_type'] = exception_type
            info['error'] = error
        else:
            info['name'] = layer.name

        output.append(info)
        if verbosity > 0:
            print >> console, msg
    return output
