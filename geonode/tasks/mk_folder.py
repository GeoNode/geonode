
from pprint import pprint

import celery
import logging, traceback
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.tasks import execute
from django.core.mail import send_mail
from geonode import settings

ROOT_DIRECTORY=""

@celery.task(name="geonode.tasks.mk_folder.create_folder",queue="mk_folder")
def create_folder(username):
    try:
        pprint("hallo thar create_folder")
        result = execute(fab_create_folder, username)
        pprint(result)
        return result
    except Exception as e:
        mail_on_error(username,  traceback.format_exc())
        pprint(traceback.format_exc())
        return e
        

@hosts(settings.GEOSTORAGE_HOST)
def fab_create_folder(username):
    return run("/mnt/geostorage/scripts/set_acls/createdir.sh {0}".format(username))


def mail_on_error(username, trace_error):
    mail_subject = "Folder creation failed for {0}".format(username)
    mail_body = "" + trace_error
    
    send_mail(mail_subject, mail_body, settings.FTP_AUTOMAIL, settings.LIPAD_SUPPORT_MAIL, fail_silently= False)
