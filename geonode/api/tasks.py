from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import shared_task
from django.conf import settings


@shared_task
def send_user_download_link(data, request):

    db_logger = logging.getLogger('db')

    # 3. Take group name and layers ...
    if data['group'] != '':
        from geonode.groups.models import GroupProfile
        from geonode.layers.models import Layer
        from django.core.mail import send_mail
        from django.db import connection
        import time
        import hashlib
        import uuid
        import zipfile
        import requests
        import shutil
        import json

        now = time.time()

        group_name = GroupProfile.objects.get(id=int(data['group']))

        hash_str = str(group_name.title) + "_" + str(now)

        folder_name = hashlib.sha224(hash_str).hexdigest()

        # create folder with folder_name
        # settings.MEDIA_ROOT+"/exports/"+folder_name
        download_dir = settings.MEDIA_ROOT + "/exports/" + folder_name
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # collects layers
        layer_ids = [int(x) for x in data['layers']]
        layer_list = Layer.objects.filter(pk__in=layer_ids)

        if 'access_token' in request.session:
            access_token = request.session['access_token']
        else:
            u = uuid.uuid1()
            access_token = u.hex

        for l in layer_list:
            download_link = settings.GEOSERVER_LOCATION + "wfs?format_options=charset%3AUTF-8&typename=" + str(
                l.typename).replace(":",
                                    "%3A") + "&outputFormat=SHAPE-ZIP&version=1.0.0&service=WFS&request=GetFeature&access_token=" + access_token
            r = requests.get(download_link)
            zfile = open(download_dir + '/' + l.name + '.zip', 'wb')
            zfile.write(r.content)
            zfile.close()
            r.close()

            zip_ref = zipfile.ZipFile(download_dir + '/' + l.name + '.zip', 'r')
            zip_ref.extractall(download_dir + '/' + l.name)
            zip_ref.close()

            os.remove(download_dir + '/' + l.name + '.zip')

            # dump the content in table_name.json
            with connection.cursor() as cursor:
                # cursor.execute("select * from " + str(l.name))
                cursor.execute("SELECT ROW_TO_JSON(t) FROM (SELECT * FROM "+str(l.name)+") t")

                all_data = cursor.fetchall()

                table_data = json.dumps(all_data)
                out = open(download_dir + '/' + l.name + '/' + l.name + ".json", "w")
                out.write(table_data)
                out.close()

            # saving metadata
            meta_data = open(download_dir + '/' + l.name + '/' + l.name + "_meta_data.xml", "w")
            meta_data.write(l.metadata_xml)
            meta_data.close()

        # keep the location of folder with folder_name for zip and create download link
        # download all layers in that folder
        zip_file = zipfile.ZipFile(download_dir + '.zip', "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(download_dir + '/')
        for root, dirs, files in os.walk(download_dir + '/'):
            for f in files:
                absname = os.path.abspath(os.path.join(root, f))
                arcname = absname[len(abs_src) + 1:]
                zip_file.write(absname, arcname)

        zip_file.close()
        # after creating zip and delete 'un zipped folder'
        shutil.rmtree(download_dir)

        org_download_link = request.META['HTTP_HOST'] + "/download/" + folder_name + ".zip"

        # Send email
        subject = 'Download Organizations Layers'
        from_email = settings.EMAIL_FROM
        message = 'This is my test message'
        recipient_list = [str(request.user.email)]  # str(request.user.email)
        html_message = "<a href='" + org_download_link + "'>Please go to the following link to download organizations layers:</a> <br/><br/><br/>" + org_download_link

        try:

            send_mail(subject=subject, message=html_message, from_email=from_email, recipient_list=recipient_list,
                      fail_silently=False, html_message=html_message)
        except Exception as e:
            # print e
            db_logger.exception(e)
