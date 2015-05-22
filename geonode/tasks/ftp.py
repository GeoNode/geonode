from __future__ import with_statement
import celery, os, traceback, re, sys, traceback
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.tasks import execute
from django.core.mail import send_mail
from geonode import settings
from geonode.cephgeo.models import FTPRequest, FTPStatus

from pprint import pprint

FTP_USERS_DIRS = {  "test-ftp-user" : "/mnt/FTP/PL1/testfolder", }
env.skip_bad_hosts = True
env.warn_only = True

class UsernameException(Exception):
    pass

class UnauthenticatedUserException(Exception):
    pass

@hosts('cephaccess@cephaccess.lan.dream.upd.edu.ph')
def fab_create_ftp_folder(ftp_request, ceph_obj_list_by_data_class):
    """
        Creates an FTP folder for the requested tile data set
        Records the request in the database
        If an existing record already exists, counts the duplicates (?)
    """
    username = ftp_request.user.username
    user_email = ftp_request.user.email
    request_name = ftp_request.name
    user_email = [user_email.encode('utf8'),]
    try:
        ftp_dir = os.path.join(get_folder_from_username(username), request_name)
        dl_script_path = "/home/cephaccess/ftp_scripts/download.py"
        email = None
        
        result = run("[ -d {0} ]".format(ftp_dir))
        if result.return_code == 0:
            print("Error on FTP request: A request has already been made this day. Please try again on the next day.")
            ftp_request.status = FTPStatus.DUPLICATE
            mail_msg = """\
An error was encountered on your FTP request named [{0}] for user [{1}]. 
A request has already been made this day. Only 1 FTP request per user is allowed 
each day. Please try again on the next day.""".format(request_name, username)
            
            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: Max daily FTP request is 1. Limit reached."

        result = run("mkdir -p {0}".format(ftp_dir))    # Create toplevel directory for this FTP request
        if result.return_code is 0:
            with cd(ftp_dir):

                for data_class, ceph_obj_list in ceph_obj_list_by_data_class.iteritems():
                    type_dir = data_class.replace(" ", "_")
                    
                    result = run("mkdir {0}".format(type_dir))      # Create a directory for each geo-type
                    if result.return_code is not 0:                 #Handle error
                        print("Error on FTP request: Failed to create FTP folder at [{0}]. Please notify the administrator of this error".format(ftp_dir))
                        ftp_request.status = FTPStatus.ERROR
                        mail_msg = """\
An error was encountered on your FTP request named [{0}] for user [{1}]. 
The system failed to create an dataclass folder inside the FTP folder at location [{2}]. 
Please e-mail the system administrator regarding this error.

---RESULT TRACE---

{3}""".format(request_name, username, os.path.join(ftp_dir,type_dir), result)
                        
                        mail_ftp_user(username, user_email, request_name, mail_msg)
                        return "ERROR: Failed to create internal folder [{0}].".format(os.path.join(ftp_dir,type_dir))
                        
                    obj_dl_list = " ".join(map(str,ceph_obj_list))
                    result = run("python {0} -d={1} {2}".format( dl_script_path,
                                                        os.path.join(ftp_dir,type_dir),
                                                        obj_dl_list)) # Download list of objects in corresponding geo-type folder
                    if result.return_code is not 0:                 #Handle error
                        print("Error on FTP request: Failed to download file/s for dataclass [{0}]. Please notify the administrator of this error".format(data_class))
                        ftp_request.status = FTPStatus.ERROR
                        mail_msg = """\
Error on FTP request: Cannot access Ceph Data Store [{0}]. Please notify the administrator of this error".format(ftp_dir))
mail_msg = "An error was encountered on your FTP request named [{0}] for user [{1}]. 
The system failed to download the following files: [{2}]. Either the file/s do/es not exist,
or the Ceph Data Storage is down. Please e-mail the system administrator regarding this error.

---RESULT TRACE---

{3}""".format(request_name, username, obj_dl_list, result)
                        mail_ftp_user(username, user_email, request_name, mail_msg)
                        return "ERROR: Failed to create folder [{0}].".format(ftp_dir)
                    
        else:
            print("Error on FTP request: Failed to create FTP folder at [{0}]. Please notify the administrator of this error".format(ftp_dir))
            ftp_request.status = FTPStatus.ERROR
            mail_msg = """\
An error was encountered on your FTP request named [{0}] for user [{1}]. 
The system failed to create an FTP folder at location [{2}]. Please ensure that you 
are a legitimate user and have permision to use this FTP service. If you are a 
legitimate user, please e-mail the system administrator regarding this error.

---RESULT TRACE---

{3}""".format(request_name, username, ftp_dir, result)
            
            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: Failed to create folder [{0}].".format(ftp_dir)



        # TODO
        # email user once the files have been downloaded
        print("Your FTP request has been completed. You may find your requested data under the DL directory with the name [{0}]".format(os.path.join("DL",request_name)))
        ftp_request.status = FTPStatus.DONE
        mail_msg = """\
Your FTP request named [{0}] for user [{1}] has been succesfully completed.
Please check your download folder for a new folder named [{0}].""".format(request_name, username)
        
        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "SUCCESS: FTP request successfuly completed."


    except UsernameException as e:
        print("Your FTP request has failed. No FTP folder was found for username [{0}]. Please ensure you have access rights to the FTP repository. Otherwise, please contact the system administrator regarding this error.".format(username))
        ftp_request.status = FTPStatus.ERROR
        mail_msg = """\
An error was encountered on your FTP request named [{0}] for user [{1}]. 
No FTP folder was found for username [{0}]. Please ensure you have 
access rights to the FTP repository. Otherwise, please contact the 
system administrator regarding this error.""".format(request_name, username)
        
        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "ERROR: User [{0}] has no FTP folder: ".format(e.message)
    
    except Exception as e:
        print("Your FTP request has failed. An unhandled error has occured. Please contact the system administrator regarding this error.")
        ftp_request.status = FTPStatus.ERROR
        mail_msg = """\
An unexpected error was encountered on your FTP request named [{0}] for user [{1}]. 
Please forward this mail to the system administrator.

---RESULT TRACE---

{2}""".format(request_name, username, traceback.format_exc())
        
        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "ERROR: User [{0}] has no FTP folder: ".format(e.message)
    
        
    finally:
        ftp_request.save()
        
@celery.task(name='geonode.tasks.ftp.process_ftp_request', queue='ftp')
def process_ftp_request(ftp_request, ceph_obj_list_by_data_class):
    """
        Create the a new folder containing the data requested inside 
        Geostorage-FTP directory
    """
    host_string='cephaccess@cephaccess.lan.dream.upd.edu.ph'
    #~ try:
        #~ result = execute(fab_create_ftp_folder, username, user_email, request_name, ceph_obj_list_by_data_class )
        #~ if isinstance(result.get(host_string, None), BaseException):
            #~ raise Exception(result.get(host_string))
    #~ except Exception as e:
        #~ traceback.print_exc()
        #~ raise Exception("task process_ftp_request terminated with exception -- %s" % e.message)
    result = execute(fab_create_ftp_folder, ftp_request, ceph_obj_list_by_data_class )
    if isinstance(result.get(host_string, None), BaseException):
        raise Exception(result.get(host_string))

@celery.task(name='geonode.tasks.ftp.check_cephaccess', queue='ftp')
def check_cephaccess():
    # NOTE: DO NOT CALL ASYNCHRONOUSLY (check_cephaccess.delay())
    #       OTHERWISE, NO OUTPUT WILL BE MADE
    """
        Call to check if CephAccess is up and running
    """
    
    #TODO: more detailed checks
    ## DONE: Check if DL folder is writeable
    ## Check from inside Cephaccess if Ceph Object Gateway is reachable
    ## 
    
    test_file = '/home/cephaccess/testfolder/DL/test.txt'
    result = run("touch {0} && rm -f {0}".format(test_file))
    if result is not 0:
        raise Exception("Unable to access {0}. Host may be down or there may be a network problem.".format(result.get(host_string)))
    
###
#   UTIL FUNCTIONS
###
def get_folder_from_username(username):
    if not username:
        raise UsernameException(username)
    
    # DEBUG FTP FOLDER
    if True:
        return "/mnt/FTP/PL1/testfolder/DL/geonode_requests"
        
    suc_str = username.split("-")[0].upper()
    nums = re.findall(r'\d+',suc_str)
    
    if not nums:
        return "/mnt/FTP/PL1/{0}1/DL/geonode_requests".format(suc_str)
    else:
        return "/mnt/FTP/PL{0}/{1}/DL/geonode_requests".format(nums[0],suc_str)
  

def mail_ftp_user(username, user_email, mail_subject, mail_msg):
    #DEBUG
    mail_subject = "Phil-LiDAR FTP Request [{0}] for User [{1}]".format(mail_subject,username)
    mail_body = """\

This is an automated mailer. DO NOT REPLY TO THIS MAIL! Send your e-mails to the site administrator.

This is an e-mail regarding your FTP request from geonode.dream.upd.edu.ph. Details are found below:

"""+mail_msg
    args_tup = (mail_subject, mail_body, settings.FTP_AUTOMAIL,
                     user_email, False)
    #pprint(args_tup)
    send_mail(mail_subject, mail_body, settings.FTP_AUTOMAIL,
                     user_email, fail_silently=False)
    #~ return
