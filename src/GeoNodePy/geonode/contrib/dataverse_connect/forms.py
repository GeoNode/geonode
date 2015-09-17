from django import forms

class ShapefileImportDataForm(forms.Form):

    # required
    title = forms.CharField()
    abstract = forms.CharField(widget=forms.Textarea)
    dv_user_email = forms.EmailField('Dataverse user email')
    shapefile_name = forms.CharField()

    # optional
    keywords = forms.CharField(max_length=255, required=False)
    worldmap_username = forms.CharField(max_length=100, required=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.shapefile_name)