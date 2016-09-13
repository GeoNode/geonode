import sys
from datetime import datetime
from django.utils.translation import ugettext as _

from django import forms 

from geonode.contrib.dataverse_layer_metadata.models import DataverseLayerMetadata
from shared_dataverse_information.dataverse_info.forms import DataverseInfoValidationForm                
from shared_dataverse_information.dataverse_info.forms_existing_layer import CheckForExistingLayerForm
DATETIME_PAT_STR = '%Y-%m-%d %H:%M'


        
class DataverseLayerMetadataAdminForm(forms.ModelForm):
    class Meta:
        model = DataverseLayerMetadata
        widgets = {  'dataverse_description': forms.Textarea(attrs={'rows': 2, 'cols':70})\
                   , 'dataset_description': forms.Textarea(attrs={'rows': 2, 'cols':70})\
              # , 'name': forms.TextInput(attrs={'size':20}) 
               }
         
class DataverseLayerMetadataValidationForm(DataverseInfoValidationForm):
    """Used to validate incoming data from GeoConnect
    Excludes the map_layer attribute and create/modtimes
    """
    
    @staticmethod
    def format_datafile_create_datetime(datetime_info):
        """
        Convert a string to a datetime object (if needed)
        example input

        success: (True, datetime object)
        fail: (False, datetime object)
        """
        if datetime_info is None:
            return (False, "The datetime cannot be None")

        if type(datetime_info) is datetime:
            return (True, datetime_info)

        if len(datetime_info) < 20:
            return (False, "The datetime string should be in this format: %s" % DATETIME_PAT_STR)


        try:
            dt_obj = datetime.strptime(datetime_info[:16], DATETIME_PAT_STR)
            return (True, dt_obj)
        except:
            e = sys.exc_info()[0]
            #print 'error: %s' % e
            return (False, "This is not a valid datetime string.  The datetime string should be in this format: %s" % DATETIME_PAT_STR)


    class Meta:
        model = DataverseLayerMetadata
        exclude = ['map_layer','created', 'modified']


class CheckForExistingLayerFormWorldmap(CheckForExistingLayerForm):
    """
    Used for the API that retrieves a WorldMap Layer based on a specific:
        - Dataverse file id
        - Dataverse installation name
    """
         
    def legitimate_layer_exists(self, post_dict):
        """
        Make sure that this layer has an associated DataverseLayerMetadata object.
        
        Note: the layer_name (for styling) does not contain the "geonode:" prefix.
            This is the reason for the __endswith in the query
        """
        assert hasattr(self, 'cleaned_data'), 'Form is invalid.  cleaned_data is not available'
        assert hasattr(post_dict, 'has_key'), "post_dict must be a dictionary-like object ('has_key' not found)"
        assert post_dict.has_key('layer_name'), "post_dict must contain a layer_name key"

        
        if DataverseLayerMetadata.objects.filter(**self.cleaned_data\
                        ).filter(map_layer__typename__endswith=post_dict.get('layer_name')\
                        ).count() > 0:
            return True
             
        return False

         
    def get_latest_dataverse_layer_metadata(self):
        """
        Return DataverseLayerMetadata objects that match the given 'dataverse_installation_name' and 'datafile_id'
        """
        assert hasattr(self, 'cleaned_data'), 'Form is invalid.  cleaned_data is not available'

        # using pre 1.6 version of Django, so can't use 'first()'
        #return DataverseLayerMetadata.objects.select_related('map_layer').filter(**self.cleaned_data).first()
        
        qs = DataverseLayerMetadata.objects.filter(**self.cleaned_data)
        r = list(qs[:1])
        #print ('r', r)
        if r:
            return r[0]
        return None
    