import datetime
import itertools

from django.conf import settings
from django.core.mail import send_mail
from django.db import models, IntegrityError
from django.template.loader import render_to_string
from django.utils.hashcompat import sha_constructor
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from taggit.managers import TaggableManager

from geonode.layers.models import Layer
from geonode.maps.models import Map


class Group(models.Model):
    
    title = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    logo = models.FileField(upload_to="people_peoplegroup", blank=True)
    description = models.TextField()
    keywords = TaggableManager(_('keywords'), help_text=_("A space or comma-separated list of keywords"), blank=True)
    access = models.CharField(max_length=15, choices=[
        ("public", _("Public")),
        ("public-invite", _("Public (invite-only))")),
        ("private", _("Private")),
    ])
    
    @classmethod
    def groups_for_user(cls, user):
        if user.is_authenticated():
            if user.is_superuser:
                return cls.objects.all()
            return cls.objects.exclude(access="private") | cls.objects.filter(groupmember__user=user)
        else:
            return cls.objects.exclude(access="private")
    
    def __unicode__(self):
        return self.title
    
    def member_queryset(self):
        return self.groupmember_set.all()
    
    def user_is_member(self, user):
        if not user.is_authenticated():
            return False
        return user.id in self.member_queryset().values_list("user", flat=True)
    
    def user_is_role(self, user, role):
        if not user.is_authenticated():
            return False
        return self.member_queryset().filter(user=user, role=role).exists()
    
    def can_view(self, user):
        if self.access == "private":
            return user.is_authenticated() and self.user_is_member(user)
        else:
            return True
    
    def can_invite(self, user):
        if not user.is_authenticated():
            return False
        return self.user_is_role(user, "manager")
    
    def join(self, user, **kwargs):
        GroupMember(group=self, user=user, **kwargs).save()
    
    def invite(self, user, from_user, role="member", send=True):
        params = dict(role=role, from_user=from_user)
        if isinstance(user, User):
            params["user"] = user
            params["email"] = user.email
        else:
            params["email"] = user
        bits = [
            settings.SECRET_KEY,
            params["email"],
            str(datetime.datetime.now()),
            settings.SECRET_KEY
        ]
        params["token"] = sha_constructor("".join(bits)).hexdigest()
        
        # If an invitation already exists, re-use it.
        try:
            invitation = self.invitations.create(**params)
        except IntegrityError:
            invitation = self.invitations.get(group=self, email=params["email"])
        
        if send:
            invitation.send(from_user)
        return invitation

    @models.permalink
    def get_absolute_url(self):
        return ('group_detail', (), { 'slug': self.slug })


class GroupMember(models.Model):
    
    group = models.ForeignKey(Group)
    user = models.ForeignKey(User)
    role = models.CharField(max_length=10, choices=[
        ("manager", _("Manager")),
        ("member", _("Member")),
    ])
    joined = models.DateTimeField(default=datetime.datetime.now)


class GroupInvitation(models.Model):
    
    group = models.ForeignKey(Group, related_name="invitations")
    token = models.CharField(max_length=40)
    email = models.EmailField()
    user = models.ForeignKey(User, null=True, related_name="pg_invitations_received")
    from_user = models.ForeignKey(User, related_name="pg_invitations_sent")
    role = models.CharField(max_length=10, choices=[
        ("manager", _("Manager")),
        ("member", _("Member")),
    ])
    state = models.CharField(
        max_length = 10,
        choices = (
            ("sent", _("Sent")),
            ("accepted", _("Accepted")),
            ("declined", _("Declined")),
        ),
        default = "sent",
    )
    created = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return "%s to %s" % (self.email, self.group.title)

    class Meta:
        unique_together = [("group", "email")]
    
    def send(self, from_user):
        current_site = Site.objects.get_current()
        domain = unicode(current_site.domain)
        ctx = {
            "invite": self,
            "group": self.group,
            "from_user": from_user,
            "domain": domain,
        }
        subject = render_to_string("groups/email/invite_user_subject.txt", ctx)
        message = render_to_string("groups/email/invite_user.txt", ctx)
        # TODO Send a notification rather than a mail
        #send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.email])
    
    def accept(self, user):
        if not user.is_authenticated():
            raise ValueError("You must log in to accept invitations")
        if not user.email == self.email:
            raise ValueError("You can't accept an invitation that wasn't for you")
        self.group.join(user, role=self.role)
        self.state = "accepted"
        self.user = user
        self.save()
    
    def decline(self, user):
        if not user.is_authenticated():
            raise ValueError("You must log in to decline invitations")
        if not user.email == self.email:
            raise ValueError("You can't decline an invitation that wasn't for you")
        self.state = "declined"
        self.save()

class GroupLayer(models.Model):
    
    group = models.ForeignKey(Group)
    layer = models.ForeignKey(Layer)

    @classmethod
    def layers_for_group(cls, group):
        layer_ids = cls.objects.filter(group=group).values_list('layer', flat=True)
        return Layer.objects.filter(id__in=layer_ids)

    class Meta:
        unique_together = (("group", "layer"),)


class GroupMap(models.Model):
    
    group = models.ForeignKey(Group)
    map = models.ForeignKey(Map)

    @classmethod
    def maps_for_group(cls, group):
        map_ids = cls.objects.filter(group=group).values_list('map', flat=True)
        return Map.objects.filter(id__in=map_ids)

    class Meta:
        unique_together = (("group", "map"),)
