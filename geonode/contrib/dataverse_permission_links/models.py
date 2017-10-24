"""
Allow specified Dataverse users who also have WorldMap credentials to:
 - Edit their Dataverse-created layers by logging into WorldMap

reference: https://github.com/IQSS/dataverse/issues/3469
"""
from django.db import models
#from django.contrib.auth import get_user_model as user_model
#User = user_model()
from geonode.people.models import Profile as User

class DataversePermissionLink(models.Model):
    """
    Scenario: A user maps a data file via the Dataverse-WorldMap connection.
    This results in a new layer.

    "Usual case"
    - Normally, these new layers are owned by a Dataverse service account.
    (This service account is a "normal" WorldMap account)

    "Extra Permissions Case"
    - In some cases case, ownership permissions for the new layer should
    also be given to additional WorldMap users, such as the BARI WorldMap user

    """
    name = models.CharField(max_length=255,
                            blank=True,
                            help_text='auto-filled on save')

    dataverse_username = models.CharField('Dataverse username',
                                          max_length=255)

    worldmap_username = models.CharField('Worldmap username',
                                         max_length=255,
                                         help_text='(Validated on save)')
    worldmap_user = models.ForeignKey(User,
                                      blank=True,
                                      null=True,
                                      help_text='auto-filled on save')

    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, help_text='optional')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Set the name attribute on save"""
        try:
            self.worldmap_user = User.objects.get(username=self.worldmap_username)
        except:
            raise Exception('Username does not exist: %s' % worldmap_username)

        if self.worldmap_user:
            self.name = '%s <--> %s' % (self.dataverse_username,
                                     self.worldmap_user.username)
            self.name = self.name[:255]

        super(DataversePermissionLink, self).save(*args, **kwargs)

    def __unicode__(self):
        if not self.name:
            return 'dv-wm link (un named)'
        return self.name

    class Meta:
        """Model Meta info"""
        unique_together = ('dataverse_username', 'worldmap_user')
        db_table = 'dataverse_permission_links'
