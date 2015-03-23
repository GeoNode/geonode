from __future__ import with_statement
from django.conf import settings
import celery
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.tasks import execute

import os

FTP_USERS_DIRS = {  "test-ftp-user" : "/mnt/FTP/PL1/testfolder", }
env.skip_bad_hosts = True
env.warn_only = True

class UsernameException(Exception):
    pass

@hosts('cephaccess@cephaccess.lan.dream.upd.edu.ph')
def fab_create_ftp_folder(username, user_email, request_name, ceph_obj_list_by_geotype):
    try:
        ftp_dir = os.path.join(get_folder_from_username(username), request_name)
        dl_script_path = "/home/cephaccess/ftp_scripts/download.py"
        
        # TODO: Check if user FTP directory exists

        result = run("mkdir {0}".format(ftp_dir))    # Create toplevel directory for this FTP request
        if result.return_code is 0:
            with cd(ftp_dir):

                for geotype, ceph_obj_list in ceph_obj_list_by_geotype.iteritems():
                    type_dir = geotype.replace(" ", "_")
                    run("mkdir {0}".format(type_dir))    # Create a directory for each geo-type

                    obj_dl_list = " ".join(map(str,ceph_obj_list))
                    run("python {0} -d={1} {2}".format( dl_script_path,
                                                        os.path.join(ftp_dir,type_dir),
                                                        obj_dl_list)) # Download list of objects in corresponding geo-type folder
        else:
            # TODO:
            # Email user stating that an FTP request has been made on this day already (max 1 ftp request per day)
            print("Error on FTP request: A request has already been made this day. Please try again on the next day.")
            return "ERROR: Max daily FTP request is 1. Limit reached."



        # TODO
        # email user once the files have been downloaded
        print("Your FTP request has been completed. You may find your requested data under the DL directory with the name [{0}]".format(os.path.join("DL",request_name)))
        return "SUCCESS: FTP request successfuly completed."


    except UsernameException as e:
        # TODO
        # Email user stating that there is no assigned 
        print("Your FTP request has failed. No FTP folder was found for username [{0}]. Please ensure you have access rights to the FTP repository. Otherwise, please contact the system administrator regarding this error.".format(username))
        return "ERROR: User [{0}] has no FTP folder: ".format(e.message)

@celery.task(name='geonode.tasks.ftp.process_ftp_request', queue='ftp')
def process_ftp_request(username, user_email, request_name, ceph_obj_list_by_geotype):
    """
        Create the a new folder containing the data requested inside 
        Geostorage-FTP directory
    """
    host_string='cephaccess@cephaccess.lan.dream.upd.edu.ph'
    try:
        result = execute(fab_create_ftp_folder, username, user_email, request_name, ceph_obj_list_by_geotype )
        if isinstance(result.get(host_string, None), BaseException):
            raise Exception(result.get(host_string))
    except Exception as e:
        raise Exception("task process_ftp_request terminated with exception -- %s" % e.message)

###
#   UTIL FUNCTIONS
###
import re
def get_folder_from_username(username):
    if not username:
        raise UsernameException(username)
    if username == 'test-ftp-user':
        return "/mnt/FTP/PL1/testfolder/DL"
        
    suc_str = username.split("-")[0].upper()
    nums = re.findall(r'\d+',suc_str)
    
    if not nums:
        return "/mnt/FTP/PL1/{0}1/DL".format(suc_str)
    else:
        return "/mnt/FTP/PL{0}/{1}/DL".format(nums[0],suc_str)
