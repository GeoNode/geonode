from django import forms
from django.core.validators import email_re
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User

from geonode.contrib.groups.models import Group
from geonode.maps.models import Map, Layer


class GroupForm(forms.ModelForm):
    
    slug = forms.SlugField(max_length=20,
            help_text=_("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
            widget=forms.HiddenInput,
            required=False
        )
            
    def clean_slug(self):
        if Group.objects.filter(slug__iexact=self.cleaned_data["slug"]).count() > 0:
            raise forms.ValidationError(_("A group already exists with that slug."))
        return self.cleaned_data["slug"].lower()
    
    def clean_title(self):
        if Group.objects.filter(title__iexact=self.cleaned_data["title"]).count() > 0:
            raise forms.ValidationError(_("A group already exists with that title."))
        return self.cleaned_data["title"]
    
    def clean(self):
        cleaned_data = self.cleaned_data
        
        title = cleaned_data.get("title")
        slug = slugify(title)
        
        cleaned_data["slug"] = slug
        
        return cleaned_data
        
    class Meta:
        model = Group


class GroupUpdateForm(forms.ModelForm):
    
    def clean_title(self):
        if Group.objects.filter(title__iexact=self.cleaned_data["title"]).count() > 0:
            if self.cleaned_data["title"] == self.instance.title:
                pass  # same instance
            else:
                raise forms.ValidationError(_("A group already exists with that title."))
        return self.cleaned_data["title"]
    
    class Meta:
        model = Group


class GroupMemberForm(forms.Form):
    role = forms.ChoiceField(choices=[
        ("member", "Member"),
        ("manager", "Manager"),
    ])
    user_identifiers = forms.CharField(widget=forms.TextInput(attrs={'class': 'user-select'}))

    def clean_user_identifiers(self):
        value = self.cleaned_data["user_identifiers"]
        new_members, errors = [], []
        
        for ui in value.split(","):
            ui = ui.strip()
            
            if email_re.match(ui):
                try:
                    new_members.append(User.objects.get(email=ui))
                except User.DoesNotExist:
                    new_members.append(ui)
            else:
                try:
                    new_members.append(User.objects.get(username=ui))
                except User.DoesNotExist:
                    errors.append(ui)
        
        if errors:
            message = ("The following are not valid email addresses or "
                "usernames: %s; not added to the group" % ", ".join(errors))
            raise forms.ValidationError(message)
        
        return new_members
    

class GroupInviteForm(forms.Form):
    
    invite_role = forms.ChoiceField(label="Role", choices=[
        ("member", "Member"),
        ("manager", "Manager"),
    ])
    invite_user_identifiers = forms.CharField(label="E-mail addresses list", widget=forms.Textarea)
    
    def clean_user_identifiers(self):
        value = self.cleaned_data["invite_user_identifiers"]
        invitees, errors = [], []
        
        for ui in value.split(","):
            ui = ui.strip()
            
            if email_re.match(ui):
                try:
                    invitees.append(User.objects.get(email=ui))
                except User.DoesNotExist:
                    invitees.append(ui)
            else:
                try:
                    invitees.append(User.objects.get(username=ui))
                except User.DoesNotExist:
                    errors.append(ui)
        
        if errors:
            message = ("The following are not valid email addresses or "
                "usernames: %s; no invitations sent" % ", ".join(errors))
            raise forms.ValidationError(message)
        
        return invitees

