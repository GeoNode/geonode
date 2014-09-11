from django.forms import ModelForm
from geonode.dataverse_info.models import DataverseInfo

# Create the form class.
class DataverseInfoValidationForm(ModelForm):
    """Used to validate incoming data from GeoConnect
    Excludes the map_layer attribute and create/modtimes
    """
    class Meta:
        model = DataverseInfo
        exclude = ['map_layer','created', 'modified']
