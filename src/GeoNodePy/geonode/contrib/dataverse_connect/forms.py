from django import forms


class DataverseLayerIndentityForm(forms.Form):

    dataverse_installation_name = forms.CharField(help_text='url to Harvard Dataverse, Odum Institute Dataverse, etc')
    datafile_id = forms.IntegerField(help_text='id in database')  # for API calls.
    #geonode_layer_name = forms.CharField('layer_typename')