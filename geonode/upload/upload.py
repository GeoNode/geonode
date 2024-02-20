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
Provide views and business logic of doing an upload.

The upload process may be multi step so views are all handled internally here
by the view function.

The pattern to support separation of view/logic is each step in the upload
process is suffixed with "_step". The view for that step is suffixed with
"_step_view". The goal of separation of view/logic is to support various
programmatic uses of this API. The logic steps should not accept request objects
or return response objects.

State is stored in a UploaderSession object stored in the user's session.
This needs to be made more stateful by adding a model.
"""
import logging


logger = logging.getLogger(__name__)


class UploaderSession:
    """All objects held must be able to survive a good pickling"""

    # the gsimporter session object
    import_session = None

    # if provided, this file will be uploaded to geoserver and set as
    # the default
    import_sld_file = None

    # location of any temporary uploaded files
    tempdir = None

    # the main uploaded file, zip, shp, tif, etc.
    base_file = None

    # the name to try to give the layer
    name = None

    # the input file charset
    charset = "UTF-8"

    # blob of permissions JSON
    permissions = None

    # store most recently configured time transforms to support deleting
    time_transforms = None

    # defaults to REPLACE if not provided. Accepts APPEND, too
    update_mode = None

    # Configure Time for this Dataset
    time = None

    # the title given to the layer
    dataset_title = None

    # the abstract
    dataset_abstract = None

    # track the most recently completed upload step
    completed_step = None

    # track the most recently completed upload step
    error_msg = None

    # the upload type - see the _pages dict in views
    upload_type = None

    # whether the files have been uploaded or provided locally
    spatial_files_uploaded = True

    # time related info - need to store here until geoserver layer exists
    time_info = None

    # whether the user has selected a time dimension for ImageMosaic granules
    # or not
    mosaic = None
    append_to_mosaic_opts = None
    append_to_mosaic_name = None
    mosaic_time_regex = None
    mosaic_time_value = None

    # the user who started this upload session
    user = None

    def __init__(self, **kw):
        for k, v in kw.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise Exception(f"not handled : {k}")

    def cleanup(self):
        """do what we should at the given state of the upload"""
        pass
