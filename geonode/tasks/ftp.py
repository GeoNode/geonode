from __future__ import with_statement
import celery
import os
import traceback
import re
import sys
import traceback
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.tasks import execute
from django.core.mail import send_mail
#from geonode import settings
from django.conf import settings
from geonode.cephgeo.models import FTPRequest, FTPStatus

import logging
import pprint
from geonode.groups.models import GroupProfile
from celery.worker.strategy import default

logger = logging.getLogger("geonode.tasks.ftp")
FTP_USERS_DIRS = {"test-ftp-user": "/mnt/FTP/PL1/testfolder", }
env.skip_bad_hosts = True
env.warn_only = True


class UserEmptyException(Exception):
    pass


class UnauthenticatedUserException(Exception):
    pass


class CephAccessException(Exception):
    pass


@hosts(settings.CEPHACCESS_HOST)
def fab_check_cephaccess(username, user_email, request_name):
    # NOTE: DO NOT CALL ASYNCHRONOUSLY (check_cephaccess.delay())
    #       OTHERWISE, NO OUTPUT WILL BE MADE
    """
        Call to check if CephAccess is up and running
    """

    # TODO: more detailed checks
    # DONE: Check if DL folder is writeable
    # Check from inside Cephaccess if Ceph Object Gateway is reachable
    ##

    test_file = '/tmp/test.txt'
    result = run("touch {0} && rm -f {0}".format(test_file))
    if result.failed:
        logger.error(
            "Unable to access {0}. Host may be down or there may be a network problem.".format(env.hosts))
        mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
A duplicate FTP request toplevel directory was found. Please wait
5 minutes in between submitting FTP requests and creating FTP folders.
If error still persists, forward this email to [{2}]""".format( request_name,
                                                                username,
                                                                settings.FTP_SUPPORT_MAIL,)

        mail_ftp_user(username, user_email, request_name, mail_msg)
        raise CephAccessException(
            "Unable to access {0}. Host may be down or there may be a network problem.".format(env.hosts))


@hosts(settings.CEPHACCESS_HOST)
def fab_create_ftp_folder(ftp_request, ceph_obj_list_by_data_class, srs_epsg=None):
    """
        Creates an FTP folder for the requested tile data set
        Records the request in the database
        If an existing record already exists, counts the duplicates (?)
    """
    username = ftp_request.user.username
    request_name = ftp_request.name
    user_email = [ftp_request.user.email.encode('utf8'), ]
    try:
        top_dir, ftp_dir = get_folders_for_user(ftp_request.user, request_name)
        dl_script_path = settings.CEPHACCESS_DL_SCRIPT
        email = None

        # Check for toplevel dir
        result = run("[ -d {0} ]".format(top_dir))
        if result.return_code == 1:
            logger.error("FTP Task Error: No toplevel directory was found.")
            ftp_request.status = FTPStatus.DUPLICATE
            mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
No top level directory was found. Please forward this email to [{2}]""".format( request_name,
                                                                                username,
                                                                                settings.FTP_SUPPORT_MAIL,)

            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: No top level directory was found."

        # Check for duplicate folders
        result = run("[ -d {0} ]".format(ftp_dir))
        if result.return_code == 0:
            logger.error(
                "FTP Task Error: A duplicate FTP request toplevel directory was found.")
            ftp_request.status = FTPStatus.DUPLICATE
            mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
A duplicate FTP request toplevel directory was found. Please wait
5 minutes in between submitting FTP requests and creating FTP folders.
If error still persists, forward this email to [{2}]""".format( request_name,
                                                                username,
                                                                settings.FTP_SUPPORT_MAIL,)

            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: A duplicate FTP request toplevel directory was found."

        # Create toplevel directory for this FTP request
        result = run("mkdir -p {0}".format(ftp_dir))
        if result.return_code is 0:
            with cd(ftp_dir):
                ln = run('ln -sf ../../../../../FAQ.txt ./')
                if ln.return_code != 0:
                    logger.error('UNABLE TO CREATE SYMLINK FOR FAQ.txt')
                else:
                    logger.info('SYMLINK CREATED')
                for data_class, ceph_obj_list in ceph_obj_list_by_data_class.iteritems():
                    type_dir = data_class.replace(" ", "_")

                    # Projection path folders
                    utm_51n_dir = os.path.join("UTM_51N", type_dir)
                    reprojected_dir = ""
                    if srs_epsg is not None:
                        reprojected_dir = os.path.join(
                            "EPSG-" + str(srs_epsg), type_dir)

                    if srs_epsg is not None:
                        if data_class == 'LAZ':
                            # Do not reproject LAZ
                            result = run("mkdir -p {0}".format(utm_51n_dir))
                        else:
                            # Create a directory for each geo-type
                            result = run(
                                "mkdir -p {0}".format(reprojected_dir))
                    else:
                        # Create a directory for each geo-type
                        result = run("mkdir -p {0}".format(utm_51n_dir))
                    if result.return_code is not 0:  # Handle error
                        logger.error(
                            "Error on FTP request: Failed to create data class subdirectory at [{0}]. Please notify the administrator of this error".format(ftp_dir))
                        ftp_request.status = FTPStatus.ERROR
                        mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
The system failed to create an dataclass subdirectory inside the FTP
folder at location [{2}]. Please forward this email to ({3})
so that we can address this issue.

---RESULT TRACE---

{4}""".format(  request_name,
                            username,
                            os.path.join(ftp_dir, type_dir),
                            settings.FTP_SUPPORT_MAIL,
                            result,)

                        mail_ftp_user(username, user_email,
                                      request_name, mail_msg)
                        return "ERROR: Failed to create data class subdirectory [{0}].".format(os.path.join(ftp_dir, type_dir))

                    obj_dl_list = " ".join(map(str, ceph_obj_list))
                    if srs_epsg is not None:
                        if data_class == 'LAZ':
                            result = run("python {0} -d={1} {2}".format(dl_script_path,
                                                                        os.path.join(
                                                                            ftp_dir, utm_51n_dir),
                                                                        obj_dl_list))  # Download list of objects in corresponding geo-type folder
                        else:
                            result = run("python {0} -d={1} -p={2} {3}".format(dl_script_path,
                                                                               os.path.join(
                                                                                   ftp_dir, reprojected_dir),
                                                                               srs_epsg,
                                                                               obj_dl_list))  # Download list of objects in corresponding geo-type folder
                    else:
                        result = run("python {0} -d={1} {2}".format(dl_script_path,
                                                                    os.path.join(
                                                                        ftp_dir, utm_51n_dir),
                                                                    obj_dl_list))  # Download list of objects in corresponding geo-type folder
                    if result.return_code is not 0:  # Handle error
                        logger.error(
                            "Error on FTP request: Failed to download file/s for dataclass [{0}].".format(data_class))
                        ftp_request.status = FTPStatus.ERROR
                        mail_msg = """\
Cannot access Ceph Data Store. An error was encountered on your data request named [{0}] for user [{1}].
The system failed to download the following files: [{2}]. Either the file/s do/es not exist,
or the Ceph Data Storage is down. Please forward this email to ({3}) that we can address this issue..

---RESULT TRACE---

{4}""".format(  request_name,
                            username,
                            obj_dl_list,
                            settings.FTP_SUPPORT_MAIL,
                            result,)
                        mail_ftp_user(username, user_email,
                                      request_name, mail_msg)
                        return "ERROR: Failed to create folder [{0}].".format(ftp_dir)

        else:
            logger.error(
                "Error on FTP request: Failed to create FTP folder at [{0}]. Please notify the administrator of this error".format(ftp_dir))
            ftp_request.status = FTPStatus.ERROR
            mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
The system failed to create the toplevel FTP directory at location [{2}].
Please ensure that you are a legitimate user and have permission to use
this FTP service. If you are a legitimate user, please e-mail the system
administrator ({3}) regarding this error.

---RESULT TRACE---

{4}""".format(  request_name,
                username,
                ftp_dir,
                settings.FTP_SUPPORT_MAIL,
                result,)

            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: Failed to create folder [{0}].".format(ftp_dir)

        # email user once the files have been downloaded
        logger.info("FTP request has been completed for user [{0}]. Requested data is found under the DL directory path [{1}]".format(
            username, os.path.join("DL", request_name)))
        ftp_request.status = FTPStatus.DONE
        mail_msg = """\
Data request named [{0}] for user [{1}] has been succesfully processed.

With your LiPAD username and password, please login with an FTPES client
like Filezilla, to ftpes://ftp.dream.upd.edu.ph. Your requested datasets
will be in a new folder named [{0}] under the directory [DL/DAD/] and will be available for 30 days only due to infrastructure limitations.

FTP Server: ftpes://ftp.dream.upd.edu.ph/
Folder location: /mnt/FTP/Others/{1}/DL/DAD/lipad_requests/{0}
Encryption: Require explicit FTP over TLS
Logon Type: Normal
Username: {1}
Password: [your LiPAD password]

Please refer to the FTP access instructions [https://lipad.dream.upd.edu.ph/help/#download-ftp]
for further information. For issues encountered, please email {2}""".format(request_name, username, settings.FTP_SUPPORT_MAIL)

        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "SUCCESS: FTP request successfuly completed."

    except UserEmptyException as e:
        logger.error(
            "FTP request has failed. No FTP folder was found for username [{0}]. User may not have proper access rights to the FTP repository.".format(username))
        ftp_request.status = FTPStatus.ERROR
        mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
No FTP folder was found for username [{1}]. Please ensure you have
access rights to the FTP repository. Otherwise, please contact the
system administrator ({2}) regarding this error.""".format(   request_name,
                                                              username,
                                                              settings.FTP_SUPPORT_MAIL)

        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "ERROR: User [{0}] has no FTP folder: ".format(e.message)

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error("""An FTP request has failed with an unexpected error:
{0}""".format(error_trace))
        ftp_request.status = FTPStatus.ERROR
        mail_msg = """\
An unexpected error was encountered on your data request named [{0}] for user [{1}].
Please forward this mail to the system administrator ({2}).

---RESULT TRACE---

{3}""".format(  request_name,
                username,
                settings.FTP_SUPPORT_MAIL,
                error_trace,)

        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "ERROR: Unexpected error occurred:\n[{0}]".format(e.message)

    finally:
        ftp_request.save()


@celery.task(name='geonode.tasks.ftp.process_ftp_request', queue='ftp')
def process_ftp_request(ftp_request, ceph_obj_list_by_data_class, srs_epsg_num=None):
    """
        Create the a new folder containing the data requested inside
        Geostorage-FTP directory
    """
    print "Processing [{0}]".format(ftp_request.name)
    host_string = settings.CEPHACCESS_HOST
    #~ try:
    #~ result = execute(fab_create_ftp_folder, username, user_email, request_name, ceph_obj_list_by_data_class )
    #~ if isinstance(result.get(host_string, None), BaseException):
    #~ raise Exception(result.get(host_string))
    #~ except Exception as e:
    #~ traceback.print_exc()
    #~ raise Exception("task process_ftp_request terminated with exception -- %s" % e.message)

    result = execute(fab_check_cephaccess, ftp_request.user.username, [
                     ftp_request.user.email.encode('utf8'), ], ftp_request.name)
    if isinstance(result.get(host_string, None), BaseException):
        raise Exception(result.get(host_string))
    else:
        result = execute(fab_create_ftp_folder, ftp_request,
                         ceph_obj_list_by_data_class, srs_epsg_num)
        if isinstance(result.get(host_string, None), BaseException):
            raise Exception(result.get(host_string))


###
#   UTIL FUNCTIONS
###
def get_folders_for_user(user, request_name):
    if not user:
        raise UserEmptyException(user)

    # Filter group if [PL1, PL2, Others, Test] ##

    groups = GroupProfile.objects.filter(
        groupmember__user=user, groupmember__role='member')

    if groups is None:
        raise CephAccessException(
            "User is not part of any FTP user group in LiPAD, no FTP folder can be found.")

    for group in groups:
        if group.slug == u'phil-lidar-1-sucs':
            # return ("/mnt/FTP/PL1/{0}/".format(user.username),
            return ("/mnt/ftp_pool/FTP/PL1/{0}/".format(user.username),
                    os.path.join(
                        # "/mnt/FTP/PL1/{0}/DL/DAD/lipad_requests".format(user.username), request_name)
                        "/mnt/ftp_pool/FTP/PL1/{0}/DL/DAD/lipad_requests".format(user.username), request_name)
                    )
        elif group.slug == u'phil-lidar-2-sucs':
            return ("/mnt/ftp_pool/FTP/PL2/{0}/".format(user.username),
                    os.path.join(
                        "/mnt/ftp_pool/FTP/PL2/{0}/DL/DAD/lipad_requests".format(user.username), request_name)
                    )
        elif group.slug == u'other-data-requesters':
            return ("/mnt/ftp_pool/FTP/Others/{0}/".format(user.username),
                    os.path.join(
                        "/mnt/ftp_pool/FTP/Others/{0}/DL/DAD/lipad_requests".format(user.username), request_name)
                    )
        elif group.slug == u'data-requesters':
            return ("/mnt/ftp_pool/FTP/Others/{0}/".format(user.username),
                    os.path.join(
                        "/mnt/ftp_pool/FTP/Others/{0}/DL/DAD/lipad_requests".format(user.username), request_name)
                    )

    raise CephAccessException(
        "User is not part of any FTP user group in LiPAD, no FTP folder can be found.")


def mail_ftp_user(username, user_email, mail_subject, mail_msg):
    # DEBUG
    mail_subject = "[LiPAD] FTP Download Request [{0}] for User [{1}]".format(
        mail_subject, username)
    mail_body = """\
This is an e-mail regarding your FTP request from LiPAD. Details are found below:

""" + mail_msg
    args_tup = (mail_subject, mail_body, settings.FTP_AUTOMAIL,
                user_email, False)
    # pprint(args_tup)
    send_mail(mail_subject, mail_body, settings.FTP_AUTOMAIL,
              user_email, fail_silently=False)
    #~ return
