import os
import tempfile
import logging
import json
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

logger = logging.getLogger("geonode.dvn.views")

@csrf_exempt
def dvn_import(request):
    print 'dvn_import'
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")
    
    print 'auth ok'
    if request.POST:
        user = None
        title = request.POST["title"]
        abstract = request.POST["abstract"]
        email = request.POST["email"]
        content = request.FILES.values()[0]
        name = request.POST["shapefile_name"]
        keywords = "" if "keywords" not in request.POST else request.POST["keywords"]

        

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
            return HttpResponse(status=500, content=json_msg, content_type="application/json")
            
        else:
            name = slugify(name.replace(".","_"))
            file_obj = write_file(content)
            try:
                saved_layer = save(name, file_obj, user,
                               overwrite = False,
                               abstract = abstract,
                               title = title,
                               keywords = keywords.split()
                )

                layer_metadata_obj = LayerMetadata(**{ 'geonode_layer_object' : saved_layer})

                json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())
                print '-' * 40
                print 'json_msg', json_msg
                return HttpResponse(status=200, content=json_msg, content_type="application/json")
                """
                return HttpResponse(status=200, content=json.dumps({
                    "success": True,
                    "layer_name": saved_layer.typename,
                    "layer_link": "%sdata/%s" % (settings.SITEURL, saved_layer.typename),
                    "embed_map_link": "%smaps/embed/?layer=%s" % (settings.SITEURL, saved_layer.typename),
                    "worldmap_username": user.username
                }))
                """
            
            except Exception, e:
                logger.error("Unexpected error during dvn import: %s : %s", name, escape(str(e)))
                err_msg = "Unexpected error during upload: %s" %  escape(str(e))
                json_msg = MessageHelperJSON.get_json_msg(success=False, msg=err_msg)
                return HttpResponse(content=json_msg, content_type="application/json")
            
    else:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Requests must be POST not GET")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")
        


@csrf_exempt
def dvn_export(request):
    return HttpResponse(status=500)

def write_file(file):
    tempdir = tempfile.mkdtemp()
    path = os.path.join(tempdir, file.name)
    with open(path, 'w') as writable:
        for c in file.chunks():
            writable.write(c)
    return path