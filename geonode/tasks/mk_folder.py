from pprint import pprint
import celery
import logging
import traceback
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.tasks import execute
from django.core.mail import send_mail

import geonode.settings as settings

ROOT_DIRECTORY = ""
env.user = settings.FABRIC_ENV_USER
env.key_filename = settings.FABRIC_ENV_KEY_FILENAME

@celery.task(name="geonode.tasks.mk_folder.create_folder", queue="mk_folder")
def create_folder(username):
    try:
        pprint("hallo thar create_folder")
        import getpass
        print 'getpass.getuser(): ' + getpass.getuser()
        print 'env.user: ' + env.user
        print 'env.key_filename: ' + env.key_filename
        result = execute(fab_create_folder, username)
        print 'result:\n' + str(result)
        return result
    except Exception as e:
        mail_on_error(username,  traceback.format_exc())
        traceback.print_exc()
        return e


@hosts(settings.FTP_HOST)
def fab_create_folder(username):
    return run(settings.FTP_SCRIPT + " {0}".format(username))
    # return run("/mnt/backup_pool/geostorage/scripts/set_acls/createdir.sh
    # {0}".format(username))
    return run(settings.FTP_SCRIPT + " {0}".format(username))


def mail_on_error(username, trace_error):
    mail_subject = "Folder creation failed for {0}".format(username)
    mail_body = "" + trace_error

    send_mail(mail_subject, mail_body, settings.FTP_AUTOMAIL, [
              settings.LIPAD_SUPPORT_MAIL], fail_silently=False)
