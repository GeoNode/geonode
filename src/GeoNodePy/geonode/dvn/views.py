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

logger = logging.getLogger("geonode.dvn.views")

@csrf_exempt
def dvn_import(request):
    if request.POST:
        user = None
        title = request.POST["title"]
        abstract = request.POST["abstract"]
        email = request.POST["email"]
        content = request.FILES.values()[0]
        name = request.POST["shapefile_name"]
        token = request.POST["geoconnect_token"]
        keywords = "" if "keywords" not in request.POST else request.POST["keywords"]

        if token != settings.DVN_TOKEN:
            return HttpResponse(status=401, content=json.dumps({
                "success": False,
                "errormsgs": "Invalid token %s" % token}))

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
            return HttpResponse(status=500, content=json.dumps({"success" : False,
                    "errormsgs": "A user account could not be created for email %s" % email}))
        else:
            name = slugify(name.replace(".","_"))
            file = write_file(content)
            try:
                saved_layer = save(name, file, user,
                               overwrite = False,
                               abstract = abstract,
                               title = title,
                               keywords = keywords.split()
                )
                return HttpResponse(status=200, content=json.dumps({
                    "success": True,
                    "layer_name": saved_layer.typename,
                    "layer_link": "%sdata/%s" % (settings.SITEURL, saved_layer.typename),
                    "embed_map_link": "%smaps/embed/?layers=%s" % (settings.SITEURL, saved_layer.typename),
                    "worldmap_username": user.username
                }))

            except Exception, e:
                logger.error("Unexpected error during dvn import: %s : %s", name, escape(str(e)))
                return HttpResponse(json.dumps({
                    "success": False,
                    "errormsgs": ["Unexpected error during upload: %s" %  escape(str(e))]}))




    else:
        return HttpResponse(status=401, content=json.dumps({
            "success": False,
            "errormsgs": "Requests must be POST not GET"}))


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