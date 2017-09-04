from __future__ import with_statement

import logging
import os
import traceback

from django.conf import settings
from django.core.mail import send_mail

from fabric.api import (
    cd,
    env,
    hosts,
    run,
)
from fabric.tasks import execute
import celery

from geonode.cephgeo.models import FTPStatus

from geonode.groups.models import GroupProfile

from geonode.automation.models import CephDataObjectResourceBase
from geonode import local_settings
from fabric.contrib.files import upload_template

logger = logging.getLogger("geonode.tasks.ftp")
FTP_USERS_DIRS = {"test-ftp-user": "/mnt/ftp_pool/FTP/PL1/testfolder", }
env.skip_bad_hosts = True
env.warn_only = True
env.shell = '/usr/local/bin/bash -l -c'


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
            "Unable to access {0}. Host may be down or there may be a network \
problem.".format(env.hosts))
        mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
A duplicate FTP request toplevel directory was found. Please wait
5 minutes in between submitting FTP requests and creating FTP folders.
If error still persists, forward this email to [{2}]""".format(
            request_name,
            username,
            settings.FTP_SUPPORT_MAIL,)

        mail_ftp_user(username, user_email, request_name, mail_msg)
        raise CephAccessException(
            "Unable to access {0}. Host may be down or there may be a network \
problem.".format(env.hosts))


@hosts(settings.CEPHACCESS_HOST)
def fab_create_ftp_folder(ftp_request, ceph_obj_list_by_data_class,
                          srs_epsg=None):
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
        python_path = settings.CEPHACCESS_PYTHON
        dl_script_path = settings.CEPHACCESS_DL_SCRIPT

        # Check for toplevel dir
        result = run("[ -d {0} ]".format(top_dir))
        if result.return_code == 1:
            logger.error("FTP Task Error: No toplevel directory was found.")
            ftp_request.status = FTPStatus.DUPLICATE
            mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
No top level directory was found. Please forward this email to [{2}]""".format(
                request_name,
                username,
                settings.FTP_SUPPORT_MAIL,)

            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: No top level directory was found."

        # Check for duplicate folders
        result = run("[ -d {0} ]".format(ftp_dir))
        if result.return_code == 0:
            logger.error(
                "FTP Task Error: A duplicate FTP request toplevel directory \
was found.")
            ftp_request.status = FTPStatus.DUPLICATE
            mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
A duplicate FTP request toplevel directory was found. Please wait
5 minutes in between submitting FTP requests and creating FTP folders.
If error still persists, forward this email to [{2}]""".format(
                request_name,
                username,
                settings.FTP_SUPPORT_MAIL,)

            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: A duplicate FTP request toplevel directory was \
found."

        # Create toplevel directory for this FTP request
        result = run("mkdir -p {0}".format(ftp_dir))
        if result.return_code is 0:
            with cd(ftp_dir):
                ln = run('ln -sf ../../../../../FAQ.txt ./')
                if ln.return_code != 0:
                    logger.error('UNABLE TO CREATE SYMLINK FOR FAQ.txt')
                else:
                    logger.info('SYMLINK CREATED')
                for data_class, ceph_obj_list \
                        in ceph_obj_list_by_data_class.iteritems():
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
                            "Error on FTP request: Failed to create data class\
 subdirectory at [{0}]. Please notify the administrator of this error".format(
                                ftp_dir))
                        ftp_request.status = FTPStatus.ERROR
                        mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
The system failed to create an dataclass subdirectory inside the FTP
folder at location [{2}]. Please forward this email to ({3})
so that we can address this issue.

---RESULT TRACE---

{4}""".format(request_name,
                            username,
                            os.path.join(ftp_dir, type_dir),
                            settings.FTP_SUPPORT_MAIL,
                            result,)

                        mail_ftp_user(username, user_email,
                                      request_name, mail_msg)
                        return "ERROR: Failed to create data class subdirectory\
 [{0}].".format(os.path.join(ftp_dir, type_dir))

                    obj_dl_list = " ".join(map(str, ceph_obj_list))
                    if srs_epsg is not None:
                        if data_class == 'LAZ':
                            # Download list of objects in corresponding
                            # geo-type folder
                            result = run("{0} {1} -d={2} {3}".format(
                                python_path,
                                dl_script_path,
                                os.path.join(ftp_dir, utm_51n_dir),
                                obj_dl_list))
                        else:
                            # Download list of objects in corresponding
                            # geo-type folder
                            result = run("{0} {1} -d={2} -p={3} {4}".format(
                                python_path,
                                dl_script_path,
                                os.path.join(ftp_dir, reprojected_dir),
                                srs_epsg,
                                obj_dl_list))
                    else:
                        # Download list of objects in corresponding geo-type
                        # folder
                        result = run("{0} {1} -d={2} {3}".format(
                            python_path,
                            dl_script_path,
                            os.path.join(
                                ftp_dir, utm_51n_dir),
                            obj_dl_list))
                    upload_xml(os.path.join(ftp_dir, utm_51n_dir),obj_dl_list)
                    if result.return_code is not 0:  # Handle error
                        logger.error(
                            "Error on FTP request: Failed to download file/s \
for dataclass [{0}].".format(data_class))
                        ftp_request.status = FTPStatus.ERROR
                        mail_msg = """\
Cannot access Ceph Data Store. An error was encountered on your data request \
named [{0}] for user [{1}].
The system failed to download the following files: [{2}]. Either the file/s \
do/es not exist,
or the Ceph Data Storage is down. Please forward this email to ({3}) that we \
can address this issue..

---RESULT TRACE---

{4}""".format(request_name,
                            username,
                            obj_dl_list,
                            settings.FTP_SUPPORT_MAIL,
                            result,)
                        mail_ftp_user(username, user_email,
                                      request_name, mail_msg)
                        return "ERROR: Failed to create folder [{0}].".format(
                            ftp_dir)

        else:
            logger.error(
                "Error on FTP request: Failed to create FTP folder at [{0}].\
Please notify the administrator of this error".format(ftp_dir))
            ftp_request.status = FTPStatus.ERROR
            mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
The system failed to create the toplevel FTP directory at location [{2}].
Please ensure that you are a legitimate user and have permission to use
this FTP service. If you are a legitimate user, please e-mail the system
administrator ({3}) regarding this error.

---RESULT TRACE---

{4}""".format(request_name,
              username,
              ftp_dir,
              settings.FTP_SUPPORT_MAIL,
              result,)

            mail_ftp_user(username, user_email, request_name, mail_msg)
            return "ERROR: Failed to create folder [{0}].".format(ftp_dir)

        # email user once the files have been downloaded
        logger.info("FTP request has been completed for user [{0}]. Requested \
data is found under the DL directory path [{1}]".format(
            username, os.path.join("DL", request_name)))
        ftp_request.status = FTPStatus.DONE
        mail_msg = """\
Data request named [{0}] for user [{1}] has been succesfully processed.

With your LiPAD username and password, please login with an FTPES client
like Filezilla, to ftpes://ftp.dream.upd.edu.ph. Your requested datasets
will be in a new folder named [{0}] under the directory [DL/DAD/] and will be \
available for 30 days only due to infrastructure limitations.

FTP Server: ftpes://ftp.dream.upd.edu.ph/
Folder location: /mnt/ftp_pool/FTP/Others/{1}/DL/DAD/lipad_requests/{0}
Encryption: Require explicit FTP over TLS
Logon Type: Normal
Username: {1}
Password: [your LiPAD password]

Please refer to the FTP access instructions [https://lipad.dream.upd.edu.ph/hel\
p/#download-ftp]
for further information. For issues encountered, please email {2}\
""".format(request_name, username, settings.FTP_SUPPORT_MAIL)

        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "SUCCESS: FTP request successfuly completed."

    except UserEmptyException as e:
        logger.error(
            "FTP request has failed. No FTP folder was found for username \
[{0}]. User may not have proper access rights to the FTP repository.\
".format(username))
        ftp_request.status = FTPStatus.ERROR
        mail_msg = """\
An error was encountered on your data request named [{0}] for user [{1}].
No FTP folder was found for username [{1}]. Please ensure you have
access rights to the FTP repository. Otherwise, please contact the
system administrator ({2}) regarding this error.""".format(request_name,
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
An unexpected error was encountered on your data request named [{0}] for user \
[{1}].
Please forward this mail to the system administrator ({2}).

---RESULT TRACE---

{3}""".format(request_name,
              username,
              settings.FTP_SUPPORT_MAIL,
              error_trace,)

        mail_ftp_user(username, user_email, request_name, mail_msg)
        return "ERROR: Unexpected error occurred:\n[{0}]".format(e.message)

    finally:
        ftp_request.save()


@celery.task(name='geonode.tasks.ftp.process_ftp_request', queue='ftp')
def process_ftp_request(ftp_request, ceph_obj_list_by_data_class,
                        srs_epsg_num=None):
    """
        Create the a new folder containing the data requested inside
        Geostorage-FTP directory
    """
    print "Processing [{0}]".format(ftp_request.name)
    host_string = settings.CEPHACCESS_HOST
    # try:
    # result = execute(fab_create_ftp_folder, username, user_email, request_name, ceph_obj_list_by_data_class )
    # if isinstance(result.get(host_string, None), BaseException):
    # raise Exception(result.get(host_string))
    # except Exception as e:
    # traceback.print_exc()
    # raise Exception("task process_ftp_request terminated with exception -- %s" % e.message)

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
            "User is not part of any FTP user group in LiPAD, no FTP folder \
can be found.")

    for group in groups:
        if group.slug == u'phil-lidar-1-sucs':
            return ("/mnt/ftp_pool/FTP/PL1/{0}/".format(user.username),
                    os.path.join("/mnt/ftp_pool/FTP/PL1/{0}/DL/DAD/\
lipad_requests".format(user.username), request_name))
        elif group.slug == u'phil-lidar-2-sucs':
            return ("/mnt/ftp_pool/FTP/PL2/{0}/".format(user.username),
                    os.path.join(
                        "/mnt/ftp_pool/FTP/PL2/{0}/DL/DAD/\
lipad_requests".format(user.username), request_name)
                    )
        elif group.slug == u'other-data-requesters':
            return ("/mnt/ftp_pool/FTP/Others/{0}/".format(user.username),
                    os.path.join(
                        "/mnt/ftp_pool/FTP/Others/{0}/DL/DAD/\
lipad_requests".format(user.username), request_name)
                    )
        elif group.slug == u'data-requesters':
            return ("/mnt/ftp_pool/FTP/Others/{0}/".format(user.username),
                    os.path.join(
                        "/mnt/ftp_pool/FTP/Others/{0}/DL/DAD/\
lipad_requests".format(user.username), request_name)
                    )

    raise CephAccessException(
        "User is not part of any FTP user group in LiPAD, no FTP folder can be \
found.")


def mail_ftp_user(username, user_email, mail_subject, mail_msg):
    # DEBUG
    mail_subject = "[LiPAD] FTP Download Request [{0}] for User [{1}]".format(
        mail_subject, username)
    mail_body = """\
This is an e-mail regarding your FTP request from LiPAD. Details are found \
below:

""" + mail_msg
    # args_tup = (mail_subject, mail_body, settings.FTP_AUTOMAIL,
    #             user_email, False)
    # pprint(args_tup)
    send_mail(mail_subject, mail_body, settings.FTP_AUTOMAIL,
              user_email, fail_silently=False)
    # return

def upload_xml(folder_dir,obj_dl_list):
    for grid_ref_file_name in obj_dl_list.split(" "):
        try:
            cephobj_resbase = CephDataObjectResourceBase.objects.get(name=grid_ref_file_name)
        except:
            continue
        keyword_text = ""
        if cephobj_resbase.keyword_list():
            keyword_text+="""       <gmd:descriptiveKeywords>\n         <gmd:MD_Keywords>"""
            for eachkeyword in cephobj_resbase.keyword_list():
                keyword_text+="""\n           <gmd:keyword>\n             <gco:CharacterString>%s</gco:CharacterString>\n           </gmd:keyword>"""%eachkeyword
            keyword_text+="""\n           <gmd:type>\n              <gmd:MD_KeywordTypeCode codeSpace="ISOTC211/19115" codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_KeywordTypeCode" codeListValue="theme">theme</gmd:MD_KeywordTypeCode>\n            </gmd:type>\n         </gmd:MD_Keywords>\n       </gmd:descriptiveKeywords>"""

        region_text = ""
        for eachregion in cephobj_resbase.regions.all():
            region_text +='\n       <gmd:descriptiveKeywords>\n         <gmd:MD_Keywords>\n           <gmd:keyword>\n             <gco:CharacterString>%s</gco:CharacterString>\n           </gmd:keyword>\n           <gmd:type>\n              <gmd:MD_KeywordTypeCode codeSpace="ISOTC211/19115" codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_KeywordTypeCode" codeListValue="place">place</gmd:MD_KeywordTypeCode>\n            </gmd:type>\n         </gmd:MD_Keywords>\n       </gmd:descriptiveKeywords>'%eachregion.name

        license_text = ""
        if cephobj_resbase.license:
            license_text+='       <gmd:resourceConstraints>\n         <gmd:MD_LegalConstraints>\n           <gmd:useConstraints>\n             <gmd:MD_RestrictionCode codeSpace="ISOTC211/19115" codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_RestrictionCode" codeListValue="license">license</gmd:MD_RestrictionCode>\n           </gmd:useConstraints>\n           <gmd:otherConstraints>\n             <gco:CharacterString>%s</gco:CharacterString>\n           </gmd:otherConstraints>\n         </gmd:MD_LegalConstraints>\n       </gmd:resourceConstraints>'%cephobj_resbase.license_light
            license_text+='\n       <gmd:resourceConstraints>\n         <gmd:MD_LegalConstraints>\n           <gmd:useConstraints>\n             <gmd:MD_RestrictionCode codeSpace="ISOTC211/19115" codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_RestrictionCode" codeListValue="license">license</gmd:MD_RestrictionCode>\n           </gmd:useConstraints>\n           <gmd:otherConstraints>\n             <gco:CharacterString>%s</gco:CharacterString>\n           </gmd:otherConstraints>\n         </gmd:MD_LegalConstraints>\n       </gmd:resourceConstraints>'%cephobj_resbase.license_verbose

        temporal_text = ""
        if cephobj_resbase.temporal_extent_start and cephobj_resbase.temporal_extent_end:
            temporal_text += """\n       <gmd:extent>\n         <gmd:EX_Extent>\n           <gmd:temporalElement>\n             <gmd:EX_TemporalExtent>\n               <gmd:extent>\n                 <gml:TimePeriod gml:id="T_01">\n                   <gml:beginPosition>%s</gml:beginPosition>\n                   <gml:endPosition>%s</gml:endPosition>\n                 </gml:TimePeriod>\n               </gmd:extent>\n             </gmd:EX_TemporalExtent>\n           </gmd:temporalElement>\n         </gmd:EX_Extent>\n       </gmd:extent>\n                """%(cephobj_resbase.temporal_extent_start.strftime("%c"),cephobj_resbase.temporal_extent_end.strftime("%c"))

        linkdl_text = ""
        for eachlink in cephobj_resbase.link_set.download():
            linkdl_text+='\n           <gmd:onLine>\n             <gmd:CI_OnlineResource>\n               <gmd:linkage>\n                 <gmd:URL>%(LinkURL)s</gmd:URL>\n               </gmd:linkage>\n               <gmd:protocol>\n                 <gco:CharacterString>WWW:DOWNLOAD-1.0-http--download</gco:CharacterString>\n               </gmd:protocol>\n               <gmd:name>\n                 <gco:CharacterString>%(LayerName)s.%(LinkExtension)s</gco:CharacterString>\n               </gmd:name>\n               <gmd:description>\n                 <gco:CharacterString>%(Title)s (%(LinkName)s Format)</gco:CharacterString>\n               </gmd:description>\n             </gmd:CI_OnlineResource>\n           </gmd:onLine>'%{'LinkURL': eachlink.url,'LayerName': cephobj_resbase.layer.name,'LinkExtension': eachlink.extension,'Title': cephobj_resbase.title,'LinkName':eachlink.name}
        linkows_text = ""
        for eachows in cephobj_resbase.link_set.ows():
            linkows_text+='\n           <gmd:onLine>\n             <gmd:CI_OnlineResource>\n               <gmd:linkage>\n                 <gmd:URL>%(LinkURL)s</gmd:URL>\n               </gmd:linkage>\n               <gmd:protocol>\n                 <gco:CharacterString>%(LinkType)s</gco:CharacterString>\n               </gmd:protocol>\n               <gmd:name>\n                 <gco:CharacterString>%(LinkType)s %(LayerWorkspace)s Service - Provides Layer: %(Title)s</gco:CharacterString>\n               </gmd:name>\n               <gmd:description>\n                 <gco:CharacterString>%(LinkName)s Root Endpoint.  This service contains the %(Title)s layer.</gco:CharacterString>\n               </gmd:description>\n             </gmd:CI_OnlineResource>\n           </gmd:onLine>'%{'LinkURL': eachows.url,'LinkType': eachows.link_type,'LayerWorkspace': cephobj_resbase.layer.workspace,'Title': cephobj_resbase.title,'LinkName':eachows.name}

        try:
            xml_owner={
                "Name": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.get_full_name()+"</gco:CharacterString> " if cephobj_resbase.owner.get_full_name() else 'gco:nilReason="missing">',
                "Org": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.organization+"</gco:CharacterString> " if cephobj_resbase.owner.organization else 'gco:nilReason="missing">',
                "Position": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.position+"</gco:CharacterString> " if cephobj_resbase.owner.position else 'gco:nilReason="missing">',
                "Voice": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.voice+"</gco:CharacterString> " if cephobj_resbase.owner.voice else 'gco:nilReason="missing">',
                "Fax": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.fax+"</gco:CharacterString> " if cephobj_resbase.owner.fax else 'gco:nilReason="missing">',
                "Delivery": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.delivery+"</gco:CharacterString> " if cephobj_resbase.owner.delivery else 'gco:nilReason="missing">',
                "City": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.city+"</gco:CharacterString> " if cephobj_resbase.owner.city else 'gco:nilReason="missing">',
                "Area": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.area+"</gco:CharacterString> " if cephobj_resbase.owner.area else 'gco:nilReason="missing">',
                "Zipcode": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.zipcode+"</gco:CharacterString> " if cephobj_resbase.owner.zipcode else 'gco:nilReason="missing">',
                "Country": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.country+"</gco:CharacterString> " if cephobj_resbase.owner.country else 'gco:nilReason="missing">',
                "Email": ">\n                   <gco:CharacterString>"+cephobj_resbase.owner.email+"</gco:CharacterString> " if cephobj_resbase.owner.email else 'gco:nilReason="missing">',
            }
        except:
            xml_owner={
                "Name": '',
                "Org": '',
                "Position": '',
                "Voice": '',
                "Fax": '',
                "Delivery": '',
                "City": '',
                "Area": '',
                "Zipcode": '',
                "Country": '',
                "Email": '',
            }
        try:
            xml_layer={
                "MDFormat": "<gco:CharacterString>GeoTIFF</gco:CharacterString>" if cephobj_resbase.layer.storeType == 'coverageStore' else '<gco:CharacterString>ESRI Shapefile</gco:CharacterString>',
                "CIOnlineResource": local_settings.SITEURL + cephobj_resbase.layer.get_absolute_url,
            }
        except:
            xml_layer={
                "MDFormat":'',
                "CIOnlineResource": '',
            }

        xml_context = {
            "Identifier": cephobj_resbase.uuid,
            "Language": cephobj_resbase.language,
            "Name": xml_owner['Name'],
            "Org": xml_owner['Org'],
            "Position": xml_owner['Position'],
            "Voice": xml_owner['Voice'],
            "Fax": xml_owner['Fax'],
            "Delivery": xml_owner['Delivery'],
            "City": xml_owner['City'],
            "Area": xml_owner['Area'],
            "Zipcode": xml_owner['Zipcode'],
            "Country": xml_owner['Country'],
            "Email": xml_owner['Email'],
            "InsertDate": cephobj_resbase.csw_insert_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Title": cephobj_resbase.title,
            "Date": cephobj_resbase.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "DateType": cephobj_resbase.date_type,
            "Edition": ">\n                   <gco:CharacterString>"+cephobj_resbase.edition+"</gco:CharacterString> " if cephobj_resbase.edition else 'gco:nilReason="missing">',
            "Abstract": cephobj_resbase.abstract,
            "Purpose": ">\n                   <gco:CharacterString>"+cephobj_resbase.purpose+"</gco:CharacterString> " if cephobj_resbase.purpose else 'gco:nilReason="missing">',
            "MaintenanceFrequency": """       <gmd:resourceMaintenance>
     <gmd:MD_MaintenanceInformation>
       <gmd:maintenanceAndUpdateFrequency>
         <gmd:MD_MaintenanceFrequencyCode codeSpace="ISOTC211/19115" codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_MaintenanceFrequencyCode" codeListValue="%(MaintenanceFrequency)s">%(MaintenanceFrequency)s</gmd:MD_MaintenanceFrequencyCode>
       </gmd:maintenanceAndUpdateFrequency>
     </gmd:MD_MaintenanceInformation>
   </gmd:resourceMaintenance>"""%{"MaintenanceFrequency": cephobj_resbase.maintenance_frequency} if cephobj_resbase.maintenance_frequency else {"MaintenanceFrequency": ""},
            "ThumbUrl": cephobj_resbase.get_thumbnail_url(),
            "MDFormat": xml_layer['MDFormat'],
            "Keywords": keyword_text,
            "Regions": region_text,
            "Licenses": license_text,
            "RCT": cephobj_resbase.restriction_code_type.identifier if cephobj_resbase.restriction_code_type else "",
            "ConstraintsOther": cephobj_resbase.constraints_other,
            "SRTC": cephobj_resbase.spatial_representation_type.identifier if cephobj_resbase.spatial_representation_type else "",
            "LayerCategory": ">\n         <gmd:MD_TopicCategoryCode>"+cephobj_resbase.category.identifier+"</gmd:MD_TopicCategoryCode>" if cephobj_resbase.category else 'gco:nilReason="missing">',
            "BboxX0": cephobj_resbase.bbox_x0,
            "BboxX1": cephobj_resbase.bbox_x1,
            "BboxY0": cephobj_resbase.bbox_y0,
            "BboxY1": cephobj_resbase.bbox_y1,
            "Temporal": temporal_text,
            "SupplementalInformation": cephobj_resbase.supplemental_information,
            "CIOnlineResource": xml_layer['CIOnlineResource'],
            "LinkDLText": linkdl_text,
            "LinkOWSText": linkows_text,
            "Statement": "><gco:CharacterString>"+cephobj_resbase.data_quality_statement+"</gco:CharacterString></gmd:statement>" if cephobj_resbase.data_quality_statement else 'gco:nilReason="missing"/>',
        }

        xml_file_dest = os.path.join(folder_dir,grid_ref_file_name+'.xml')
        #tree.write(grid_ref_file_name+".xml",xml_declaration=True,encoding='utf-8',method="xml")

        #Fabric append which appends/creates a file
        upload_template("ftp_metadata.xml",xml_file_dest,xml_context)
