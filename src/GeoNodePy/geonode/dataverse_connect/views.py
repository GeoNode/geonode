import os
import tempfile
import logging
import sys

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import TemporaryUploadedFile

from geonode.maps.utils import save
from geonode.maps.views import _create_new_user
from geonode.utils import slugify

#from geonode.dataverse_private_layer.permissions_helper import make_layer_private

from geonode.dataverse_connect.dataverse_auth import has_proper_auth
from geonode.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata
from geonode.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object

from geonode.dataverse_layer_metadata.layer_metadata_helper import add_dataverse_layer_metadata

logger = logging.getLogger("geonode.dataverse_connect.views")

@csrf_exempt
def view_add_worldmap_shapefile(request):
    
    logger.info('----- view_add_worldmap_shapefile -----')
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")
    
    
    if request.POST:
        
        user = None
        title = request.POST["title"]
        abstract = request.POST["abstract"]
        email = request.POST["email"]
        content = request.FILES.values()[0]
        name = request.POST["shapefile_name"]

        keywords = "" if "keywords" not in request.POST else request.POST["keywords"]

        #print request.POST.items()

        if "worldmap_username" in request.POST:
            try:
                user = User.objects.get(username=request.POST["username"])
            except:
                pass

        if user is None:
            existing_user = User.objects.filter(email=email)
            if existing_user.count() > 0:
                user = existing_user[0]
            else:
                user = _create_new_user(email, None, None, None)

        if not user:
            json_msg = MessageHelperJSON.get_json_msg(success=False, msg="A user account could not be created for email %s" % email)
            return HttpResponse(status=200, content=json_msg, content_type="application/json")
            
        else:
            name = slugify(name.replace(".","_"))
            file_obj = write_the_dataverse_file(content)
            #print ('file_obj', file_obj)
            
            try:
                
                # Save the actual layer
                saved_layer = save(name, file_obj, user,
                               overwrite = False,
                               abstract = abstract,
                               title = title,
                               keywords = keywords.split()
                )
                
                # Look for DataverseInfo in the request.POST
                #   If it exists, create a DataverseLayerMetadata object
                #
                dataverse_layer_metadata = add_dataverse_layer_metadata(saved_layer, request.POST)
                if dataverse_layer_metadata is None:
                    logger.error("Failed to create a DataverseLayerMetadata object")
                    json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Failed to create a DataverseLayerMetadata object")
                    return HttpResponse(status=200, content=json_msg, content_type="application/json")


                # Prepare a JSON reponse
                # 
                layer_metadata_obj = LayerMetadata(**{ 'geonode_layer_object' : saved_layer})

                # Return the response!
                json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())
                #print '-' * 40
                #print 'json_msg', json_msg
                
                return HttpResponse(status=200, content=json_msg, content_type="application/json")
            
            except:
                e = sys.exc_info()[0]
                logger.error("Unexpected error during dvn import: %s : %s" % (name, escape(str(e))))
                err_msg = "Unexpected error during upload: %s" %  escape(str(e))
                json_msg = MessageHelperJSON.get_json_msg(success=False, msg=err_msg)
                return HttpResponse(content=json_msg, content_type="application/json")
            
    else:
        
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request must be a POST, not GET")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")
        


def write_the_dataverse_file(temp_uploaded_file):
    """
    Save the uploaded dataverse file to disk
    """
    assert type(temp_uploaded_file) is TemporaryUploadedFile\
        , '"temp_uploaded_file" must be type "django.core.files.uploadedfile.TemporaryUploadedFile"'

    #print 'file type', type(temp_uploaded_file)

    tempdir = tempfile.mkdtemp()
    path = os.path.join(tempdir, temp_uploaded_file.name)
    with open(path, 'w') as writable:
        for c in temp_uploaded_file.chunks():
            writable.write(c)
    return path
    


"""
# Is this a private layer?
#
if dataverse_layer_metadata.dataset_is_public is False:
    #
    # Yes, set privacy permissions
    #
    if make_layer_private(saved_layer) is False:
        #
        # Failed to set privacy permissions, remove layer
        #
        logger.error("Failed to set privacy permissions.  Deleting layer")
        saved_layer.delete()
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Failed to set privacy permissions.  Deleting layer")
        return HttpResponse(status=200, content=json_msg, content_type="application/json")


"""