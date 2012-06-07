from django import forms
from geonode.people.models import Contact, ContactRole
import taggit

class RoleForm(forms.ModelForm):
    class Meta:
        model = ContactRole
        exclude = ('contact', 'layer')

class PocForm(forms.Form):
    contact = forms.ModelChoiceField(label = "New point of contact",
                                     queryset = Contact.objects.exclude(user=None))
class ContactForm(forms.ModelForm):
    keywords = taggit.forms.TagField()
    class Meta:
        model = Contact
        exclude = ('user',)
