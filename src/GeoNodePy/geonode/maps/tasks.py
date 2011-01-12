from geonode.maps.gs_helpers import _handle_layer_upload
import os, sys
from celery.decorators import task
from django import db
from django.contrib.auth.models import User
import logging

try:
    from notification import models as notification
except ImportError:
    notification = None


logger = logging.getLogger("geonode.maps.tasks")

@task
def handle_external_layer_upload(base_file_path, username):
    user = None 
    db.connection.close() # forcibly close db connection, causing it to reopen
    try:
        user = User.objects.get(username=username)
        layer_name = os.path.splitext(os.path.split(base_file_path)[1])[0]
        base_file = open(base_file_path)
        if base_file_path.lower().endswith('.shp'):
            #TODO Check for UPPER or MiXeD case file extensions
            extra_files = {}
            extra_files['dbf'] = open(base_file_path.replace('.shp', '.dbf'))
            extra_files['shx'] = open(base_file_path.replace('.shp', '.shx'))
            extra_files['prj'] = open(base_file_path.replace('.shp', '.prj'))
            layer, errors = _handle_layer_upload(layer_name=layer_name, base_file=base_file, user=user, extra_files=extra_files)   
        else:
            layer, errors = _handle_layer_upload(layer_name=layer_name, base_file=base_file, user=user)
        if(len(errors) > 0):
            logger.debug(errors)
            if notification:
                notification.send([user], "upload_failed", {'layer_name': layer_name, 'errors': errors})
            return -1
        else:
            if notification:
                notification.send([user], "upload_successful",  {'layer_name': layer_name})
            return 0
    except:
        if user and notification: 
            errors = str(sys.exc_info()[0])
            notification.send([user], "upload_failed", {'layer_name': layer_name, 'errors': errors})
        return -1 
