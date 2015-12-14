import os
import tempfile
import logging
import sys

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile
from django.core.exceptions import ValidationError

from geonode.maps.utils import save
from geonode.maps.views import _create_new_user
from geonode.utils import slugify

#from geonode.dataverse_private_layer.permissions_helper import make_layer_private

from geonode.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata
from geonode.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object

from geonode.dataverse_layer_metadata.layer_metadata_helper import add_dataverse_layer_metadata, check_for_existing_layer, update_the_layer_metadata


from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text
from shared_dataverse_information.shapefile_import.forms import ShapefileImportDataForm

logger = logging.getLogger("geonode.dataverse_connect.views")

'''
@csrf_exempt
def view_check_for_existing_layer(request):
    """
    Before sending over the actual file:
        (1) Send over the metadata
        (2) Check if a layer already exists
    """

    #   Is this request a POST?
    #
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request must be a POST.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    #   Does the request have proper auth?
    #
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    #-----------------------------------------------------------
    #   start: check for existing layer
    #   Does a layer already exist for this file?
    #   Check for an existing DataverseLayerMetadata object.
    #-----------------------------------------------------------
    dv_layer_metadata = None
    logger.info("pre existing layer check")
    print "pre existing layer check"
    try:
        existing_dv_layer_metadata = check_for_existing_layer(Post_Data_As_Dict)
        logger.info("found existing layer")
        print "found existing layer"
    except ValidationError as e:
        error_msg = "The dataverse information failed validation: %s" % Post_Data_As_Dict
        logger.error(error_msg)
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="(The WorldMap could not verify the data.)")
        return HttpResponse(status=200, content=json_msg, content_type="application/json")

    #-----------------------------------------------------------
    #   end: check for existing layer
    #   A layer was found!
    #   Update the DataverseLayerMetadata and return the layer.
    #   * Update the worldmap user? *
    #-----------------------------------------------------------
    if existing_dv_layer_metadata:
        print "Found existing layer!"
        logger.info("Found existing layer!")

        update_the_layer_metadata(existing_dv_layer_metadata, Post_Data_As_Dict)

        layer_metadata_obj = LayerMetadata(existing_dv_layer_metadata.map_layer)

        json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())
        return HttpResponse(status=200, content=json_msg, content_type="application/json")

    logger.info("Layer not yet created on WorldMap")

    json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Layer not yet created on WorldMap")

    return HttpResponse(status=200, content=json_msg, content_type="application/json")
'''


@csrf_exempt
def view_add_worldmap_shapefile(request):
    """
    Process a Dataverse POST request to create a Layer with an accompanying LayerMetadata object
    """

    #   Is this request a POST?
    #
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request must be a POST.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")


    #   Does the request have proper auth?
    #   -> check is now done by the ShapefileImportDataForm


    #   Is there a file in this request
    #
    if (not request.FILES) or len(request.FILES)==0:
        logger.error("Shapefile import error.  No FILES in request")
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="File not found.  Did you send a file?")

        return HttpResponse(status=400, content=json_msg, content_type="application/json")
    
    if not len(request.FILES)==1:
        logger.error("Shapefile import error.  Only send 1 file")
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="This request only accepts a single file")

        return HttpResponse(status=400, content=json_msg, content_type="application/json")
        
    

    Post_Data_As_Dict = request.POST.dict()

    #   Is this a valid request?  Check parameters.
    #
    form_shapefile_import= ShapefileImportDataForm(Post_Data_As_Dict)
    if not form_shapefile_import.is_valid():
        #
        #   Invalid, send back an error message
        #
        logger.error("Shapefile import error: \n%s" % format_errors_as_text(form_shapefile_import))
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Incorrect params for ShapefileImportDataForm: <br />%s" % form_shapefile_import.errors)

        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    if not form_shapefile_import.is_signature_valid_check_post(request):
        #
        #   Invalid signature on request
        #
        logger.error("Invalid signature on request.  Failed validation with ShapefileImportDataForm")
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Invalid signature on request.  Failed validation with ShapefileImportDataForm")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    #-----------------------------------------------------------
    #   start: check for existing layer
    #   Does a layer already exist for this file?
    #   Check for an existing DataverseLayerMetadata object.
    #-----------------------------------------------------------
    existing_dv_layer_metadata = None
    logger.info("pre existing layer check")
    print "pre existing layer check"
    try:
        existing_dv_layer_metadata = check_for_existing_layer(Post_Data_As_Dict)
        logger.info("found existing layer")
        print "found existing layer"
    except ValidationError as e:
        error_msg = "The dataverse information failed validation: %s" % Post_Data_As_Dict
        logger.error(error_msg)
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="(The WorldMap could not verify the data.)")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    #-----------------------------------------------------------
    #   end: check for existing layer
    #   A layer was found!
    #   Update the DataverseLayerMetadata and return the layer.
    #   * Update the worldmap user? *
    #-----------------------------------------------------------
    if existing_dv_layer_metadata:
        print "Found existing layer!"
        logger.info("Found existing layer!")

        update_the_layer_metadata(existing_dv_layer_metadata, Post_Data_As_Dict)

        layer_metadata_obj = LayerMetadata( existing_dv_layer_metadata.map_layer)

        json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())
        return HttpResponse(status=200, content=json_msg, content_type="application/json")



    #
    #   Using the ShapefileImportDataForm,
    #   get/set the attributes needed to create a layer
    #
    import_data = form_shapefile_import.cleaned_data

    title = import_data['title']
    abstract = import_data['abstract']
    dv_user_email = import_data['dv_user_email']
    worldmap_username = import_data['worldmap_username']
    shapefile_name = import_data['shapefile_name']
    keywords = import_data['keywords']

    transferred_file = request.FILES.values()[0]


    # Retrieve or create a User object
    #
    # - attempt #1 - Has a username name been sent in the request?
    # - attempt #2 - Does the dataverse email match an existing WorldMap user?
    # - attempt #3 -
    #
    user_object = get_worldmap_user_object(worldmap_username, dv_user_email)
    if user_object is None:
        error_msg = "A user account could not be created for email %s" % dv_user_email
        logger.error(error_msg)
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg=error_msg)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    #   Format file name and save actual file
    #
    shapefile_name = slugify(shapefile_name.replace(".","_"))
    file_obj = write_the_dataverse_file(transferred_file)
        #print ('file_obj', file_obj)

    #   Save the actual layer
    #
    #
    try:

        saved_layer = save(shapefile_name,\
                           file_obj,\
                           user_object,\
                           overwrite = False,\
                           abstract = abstract,\
                           title = title,\
                           keywords = keywords.split()\
                        )

        # Look for DataverseInfo in the Post_Data_As_Dict
        #   If it exists, create a DataverseLayerMetadata object
        #
        dataverse_layer_metadata = add_dataverse_layer_metadata(saved_layer, Post_Data_As_Dict)
        if dataverse_layer_metadata is None:
            logger.error("Failed to create a DataverseLayerMetadata object")
            json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Failed to create a DataverseLayerMetadata object")

            # remove the layer
            #
            if saved_layer:
                saved_layer.delete()
                
            # Error
            return HttpResponse(status=400, content=json_msg, content_type="application/json")


        # Prepare a JSON reponse
        #
        layer_metadata_obj = LayerMetadata(saved_layer)

        # Return the response!
        json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())
        #print '-' * 40
        #print 'json_msg', json_msg

        return HttpResponse(status=200, content=json_msg, content_type="application/json")

    except:
        e = sys.exc_info()[0]
        logger.error("Unexpected error during dvn import: %s : %s" % (shapefile_name, escape(str(e))))
        err_msg = "Unexpected error during upload: %s" %  escape(str(e))
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg=err_msg)
        return HttpResponse(status=500, content=json_msg, content_type="application/json")



def write_the_dataverse_file(temp_uploaded_file):
    """
    Save the uploaded dataverse file to disk
    """
    assert type(temp_uploaded_file) in (InMemoryUploadedFile, TemporaryUploadedFile)\
        , 'temp_uploaded_file" must be type "django.core.files.uploadedfile.TemporaryUploadedFile or InMemoryUploadedFile.  Found type: %s' % type(temp_uploaded_file)

    #print 'file type', type(temp_uploaded_file)

    tempdir = tempfile.mkdtemp()
    path = os.path.join(tempdir, temp_uploaded_file.name)
    with open(path, 'w') as writable:
        for c in temp_uploaded_file.chunks():
            writable.write(c)
    return path
    

def get_worldmap_user_object(worldmap_username, dv_user_email):
    """
    Retrieve or create a User object

    - attempt #1 - Is there a worldmap_username?
    - attempt #2 - Does the dataverse email match an existing WorldMap user?
    - attempt #3 - Create new user based on the dataverse email

    If all attempts fail, return None
    """
    user_object = None

    if worldmap_username:
        try:
            user_object = User.objects.get(username=worldmap_username)
            return user_object
        except:
            pass

    if dv_user_email:
        existing_users = User.objects.filter(email=dv_user_email)
        if existing_users.count() > 0:
            return existing_users[0]

    try:
        return _create_new_user(dv_user_email, None, None, None)
    except:
        logger.error('_create_new_user failed with email: %s' % dv_user_email)

    return None
"""
# Is this a private layer?
#
if dataverse_layer_metadata.dataset_is_public is False:
    #
    # Yes, set privacy permissions
    #
    if make_layer_private(saved_layer) is False:
        #
        # Failed to set privacy permissions, remove layer
        #
        logger.error("Failed to set privacy permissions.  Deleting layer")
        saved_layer.delete()
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Failed to set privacy permissions.  Deleting layer")
        return HttpResponse(status=200, content=json_msg, content_type="application/json")


"""