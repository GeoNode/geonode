from __future__ import print_function
import sys
import os
import json
import traceback
from django.core import serializers
from django.core.serializers.json import Serializer
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object

from geonode.contrib.dataverse_layer_metadata.forms import DataverseLayerMetadataValidationForm
from geonode.contrib.datatables.forms import TableUploadAndJoinRequestForm


from geonode.contrib.msg_util import *

#from .models import DataTable, JoinTarget, TableJoin
#from .utils import process_csv_file, setup_join, create_point_col_from_lat_lon, standardize_name

import logging
logger = logging.getLogger(__name__)

"""
Connecting the Dataverse to the WorldMap's Tabular API
- APIs using GeoConnect for authentication
    (Dataverse <-> GeoConnect <-> WorldMap)
"""
# check login!
# check user perms!
def view_upload_table_and_join_layer(request):
    """
    http://127.0.0.1:8000/dataverse-tabular/api/upload-join/

    :param request:
    :return:
    """
    if request.method != 'POST':
        return HttpResponse("Invalid Request", mimetype="text/plain", status=500)

    post_data_dict = request.POST.dict()

    form_upload_and_join = TableUploadAndJoinRequestForm(post_data_dict)
    if not form_upload_and_join.is_valid():

        json_msg = MessageHelperJSON.get_json_fail_msg(\
                        "Invalid Data for Upload and Join: %s" % form_upload_and_join.errors)

        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    # -------------------------------------------
    # Is the Dataverse Layer Metadata valid?
    # -------------------------------------------
    """
    if not form_upload_and_join.is_signature_valid_check_post(request):
        err_msg = "Invalid signature on request.  Failed validation with TableUploadAndJoinRequestForm"
        logger.error(err_msg)

        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg=err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)
    """

    # -------------------------------------------
    # Is the Dataverse Layer Metadata valid?
    # -------------------------------------------
    f = DataverseLayerMetadataValidationForm(Post_Data_As_Dict)
    if not f.is_valid():
        logger.error('check_for_existing_layer. failed validation')
        logger.error('Errors: %s' % f.errors)
        raise forms.ValidationError('Failed to validate dataverse_info data')

    f_dv_info = DataverseInfoValidationForm(request.POST)
    if not f_dv_info.is_valid():
        return_dict = dict(success=False\
                , msg= "Invalid Data for Upload and Join: %s" % f.errors
                  )
        return HttpResponse(json.dumps(return_dict), mimetype="application/json", status=400)

    if request.method != 'POST':
        return HttpResponse("Invalid Request", mimetype="text/plain", status=500)
