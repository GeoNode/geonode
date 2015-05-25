from django.db import models

# Create your models here.
class BaseRegistrationProfile(models.Model):
    name_of_requestor = models.CharField(
        _("Name of Requestor"),
        max_length = 255,
        required = True,
    )
    organization = models.CharField(
        _("Office/Organization Name"),
        max_length = 255,
        required = True,
    )
    local_or_foreign = models.TypedChoiceField(
        _("Are you a local or foreign entity?"),
        choices = ((0, "Local"), (1, "Foreign")),
        required = True,
    )
    intended_use = models.TypedChoiceField(
        _("Intended use of dataset?"),
        choices = ((0, "Non-commercial"), (1, "Commercial")),
        required = True,
    )
    email = models.CharField(
        _("Email of contact"),
        max_length = 255,
        required = True,
    )
    contact_number = models.CharField(
        _("Contact Number"),
        max_length = 255,
        required = True,
    )
    
    
class NonCommercialProfile(models.Model):
    #Page 1
    base_profile = models.ForeignKey(BaseRegistrationProfile, null=False, blank=False)
    
    project_summary = models.TextField(
        label = "Summary of Project/Program",
        required = True,
    )
    organization_type = models.TypedChoiceField(
        label = "Type of Organization",
        choices = ((2, "Government Agency/Local Government Unit"),
                   (3, "Academic or Research Institution"),
                   (4, "Academe"),
                   (5, "International NGO"),
                   (6, "Local NGO"),
                   (7, "Private"),
                   (8, "Other"),),
        
        required = True,
    )
    other_org_type = models.CharField(
        label = "If 'Type of Organization' is 'Other' please specify below:",
        max_length = 255,
        required = False,
    )
    
    #Page 2
    data_type_requested models.TypedChoiceField(
        label = "Type of data requested",
        choices = ((0, "Interpreted"), 
                   (1, "Raw"), 
                   (2, "Processed"), 
                   (3, "Other")),
        initial = '0',
        required = True,
    )
    other_data_type_requested = models.CharField(
        label = "If 'Type of data requested' is 'Other' please specify below:",
        max_length = 255,
        required = False,
    ) 

class AcademeProfile(models.Model):
    noncommercial_profile = models.ForeignKey(NonCommercialProfile, null=False, blank=False)
    request_level = models.TypedChoiceField(
        label = "Level of request",
        choices = ((0, "Institution"),
                   (1, "Faculty"),
                   (2, "Student"),
        
        required = True,
    )
    funding_source = models.CharField(
        label = "Source of funding",
        max_length = 255,
        required = True,
    )
    consultant_status = models.TypedChoiceField(
        label = "Are you a consultant in behalf of another organization?",
        choices = ((1, "Yes"), (0, "No")),
        coerce = lambda x: bool(int(x)),
        widget = forms.RadioSelect,
        initial = '1',
        required = True,
    )

class CommercialProfile(models.Model):
    pass

class AreaInterests(models.Model):
    province = models.CharField(
        label = "Province",
        max_length = 255,
        required = True
    )
    municipality = models.CharField(
        label = "City/Municipality",
        max_length = 255,
        required = True
    )
    
