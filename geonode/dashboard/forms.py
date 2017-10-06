from django import forms


class DataFolderBackupForm(forms.Form):
    user = forms.CharField(300)
    password = forms.CharField(widget=forms.PasswordInput())
