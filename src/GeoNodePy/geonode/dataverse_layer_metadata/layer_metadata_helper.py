from __future__ import print_function
import logging

from geonode.dataverse_layer_metadata.models import DataverseLayerMetadata
from geonode.dataverse_layer_metadata.forms import DataverseLayerMetadataValidationForm

from geonode.maps.models import Layer

logger = logging.getLogger("geonode.dataverse_layer_metadata.layer_metadata_helper")

def add_dataverse_layer_metadata(saved_layer, dataverse_info):
    """
    If a Layer has been created via Geoconnect/Dataverse, create a 
    """
    assert type(saved_layer), Layer
    assert type(dataverse_info), dict

    (success, create_datetime_obj_or_err_str) = DataverseLayerMetadataValidationForm.format_datafile_create_datetime(dataverse_info.get('datafile_create_datetime', None))

    if success is False:
        print ('failed to format datetime', create_datetime_obj_or_err_str)
        logger.error('Invalid "datafile_create_datetime"\n%s' % create_datetime_obj_or_err_str)
        return False

    dataverse_info['datafile_create_datetime'] = create_datetime_obj_or_err_str

    f = DataverseLayerMetadataValidationForm(dataverse_info)
    #print (dir(f))
    if not f.is_valid():
        print ('failed validation')
        print (f.errors)
        logger.error("Unexpected form validation error in add_dataverse_layer_metadata. dvn import: %s" % f.errors)
        return False


    # Create the DataverseLayerMetadata object
    layer_metadata = f.save(commit=False)


    # Add the related Layer object
    layer_metadata.map_layer = saved_layer

    # Save it!!
    layer_metadata.save()
    
    return True
    
