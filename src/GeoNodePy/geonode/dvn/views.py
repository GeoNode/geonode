import os
import tempfile
import logging
import sys
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from geonode.maps.utils import save
from geonode.maps.views import _create_new_user
from geonode.utils import slugify

from geonode.dvn.dataverse_auth import has_proper_auth
from geonode.dvn.layer_metadata import LayerMetadata        # object with layer metadata
from geonode.dvn.dv_utils import MessageHelperJSON          # format json response object

from geonode.dataverse_layer_metadata.layer_metadata_helper import add_dataverse_layer_metadata

logger = logging.getLogger("geonode.dvn.views")

@csrf_exempt
def dvn_import(request):
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
        #dataverse_info = request.POST.get('dataverse_info', None)
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
            file_obj = write_file(content)
            print ('file_obj', file_obj)
            
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
                add_dataverse_layer_metadata(saved_layer, request.POST)

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
        


#@csrf_exempt
#def dvn_export(request):
#    return HttpResponse(status=500)

def write_file(file):
    tempdir = tempfile.mkdtemp()
    path = os.path.join(tempdir, file.name)
    with open(path, 'w') as writable:
        for c in file.chunks():
            writable.write(c)
    return path