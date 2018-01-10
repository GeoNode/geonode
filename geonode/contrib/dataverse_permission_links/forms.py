from django import forms
#from django.contrib.auth import get_user_model as user_model
#User = user_model()
from geonode.people.models import Profile as User

class DataversePermissionLinkForm(forms.ModelForm):

    def clean_dataverse_username(self):
        """Strip whitespace from username"""
        dataverse_username = self.cleaned_data.get('dataverse_username', None)
        if dataverse_username is None:
            raise forms.ValidationError("Please enter a Dataverse username.")

        dataverse_username = dataverse_username.strip()
        if len(dataverse_username) == 0:
            raise forms.ValidationError("Please enter a Dataverse username.")

        return dataverse_username

    def clean_worldmap_username(self):
        """Make sure the worldmap username maps to an actual User object"""

        worldmap_username = self.cleaned_data.get('worldmap_username', None)
        if worldmap_username is None:
            raise forms.ValidationError("Please enter a WorldMap username.")

        worldmap_username = worldmap_username.strip()
        if len(worldmap_username) == 0:
            raise forms.ValidationError("Please enter a WorldMap username.")

        # Check if the username is valid
        try:
            worldmap_user = User.objects.get(username=worldmap_username)
            return worldmap_username
        except User.DoesNotExist:
            raise forms.ValidationError(\
                'That WorldMap username does not exist. ("%s")' % worldmap_username)

    def __init__(self, *args, **kwargs):
        """Limit WorldMap user drop down to only the selected choice"""
        super(DataversePermissionLinkForm, self).__init__(*args, **kwargs)

        selected_worldmap_user_id = kwargs.get('initial', {}).get('worldmap_user', None)

        # Is this an existing/saved DataversePermissionLinkForm
        #
        if self.instance and self.instance.id:
            # Yes, limit choices to the chosen WorldMap user
            #
            self.fields['worldmap_user'].queryset = User.objects.filter(\
                                        pk=self.instance.worldmap_user.id)

        elif selected_worldmap_user_id and selected_worldmap_user_id.isdigit():
            self.fields['worldmap_user'].queryset = User.objects.filter(\
                                        pk=selected_worldmap_user_id)


        elif 'initial' in kwargs:
            # We can't "afford" to list everything.
            # Don't list any Users
            #   - An admin template instructs the user on how
            #       to add a new JoinTarget via the Layer admin
            #
            self.fields['worldmap_user'].queryset = User.objects.none()
