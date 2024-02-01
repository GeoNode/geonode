#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import os
import logging

from shutil import copyfile
from taggit.managers import TaggableManager

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.db.models import signals
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.auth.models import Group
from django.templatetags.static import static
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from geonode.utils import build_absolute_uri
from geonode.thumbs.utils import MISSING_THUMB

from guardian.shortcuts import get_objects_for_group

logger = logging.getLogger(__name__)


class GroupCategory(models.Model):
    slug = models.SlugField(max_length=255, unique=True, null=False, blank=False)
    name = models.CharField(_("Name"), max_length=255, unique=True, null=False, blank=False)
    description = models.TextField(_("Description"), null=True, default=None, blank=True)

    class Meta:
        verbose_name_plural = _("Group Categories")

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("group_category_detail", args=(self.slug,))


def group_category_pre_save(sender, instance, *args, **kwargs):
    instance.slug = slugify(instance.name)


signals.pre_save.connect(group_category_pre_save, sender=GroupCategory)


class GroupProfile(models.Model):
    GROUP_CHOICES = [
        ("public", _("Public")),
        ("public-invite", _("Public (invite-only)")),
        ("private", _("Private")),
    ]

    access_help_text = _(
        "Public: Any registered user can view and join a public group.<br>"
        "Public (invite-only):Any registered user can view the group.  "
        "Only invited users can join.<br>"
        "Private: Registered users cannot see any details about the group, including membership.  "
        "Only invited users can join."
    )
    email_help_text = _(
        "Email used to contact one or all group members, " "such as a mailing list, shared email, or exchange group."
    )

    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    title = models.CharField(_("Title"), max_length=1000)
    slug = models.SlugField(unique=True, max_length=1000)
    logo = models.ImageField(_("Logo"), upload_to="people_group", blank=True)
    description = models.TextField(_("Description"))
    email = models.EmailField(_("Email"), null=True, blank=True, help_text=email_help_text)
    keywords = TaggableManager(_("Keywords"), help_text=_("A space or comma-separated list of keywords"), blank=True)
    access = models.CharField(
        _("Access"), max_length=15, default="public'", choices=GROUP_CHOICES, help_text=access_help_text
    )
    categories = models.ManyToManyField(GroupCategory, verbose_name=_("Categories"), blank=True, related_name="groups")
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        group, created = Group.objects.get_or_create(name=self.slug)
        self.group = group
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            Group.objects.filter(name=str(self.slug)).delete()
        except Exception as e:
            logger.exception(e)
        super().delete(*args, **kwargs)

    @classmethod
    def groups_for_user(cls, user):
        """
        Returns the groups that user is a member of.  If the user is a superuser, all groups are returned.
        """
        if user.is_authenticated:
            if user.is_superuser:
                return cls.objects.all()
            return cls.objects.filter(groupmember__user=user)
        return []

    def __str__(self):
        return str(self.title)

    def keyword_list(self):
        """
        Returns a list of the Group's keywords.
        """
        return [kw.name for kw in self.keywords.all()]

    def resources(self, resource_type=None):
        """
        Returns a generator of objects that this group has permissions on.

        :param resource_type: Filter's the queryset to objects with the same type.
        """
        queryset = get_objects_for_group(
            self.group, ["base.view_resourcebase", "base.change_resourcebase"], any_perm=True
        )

        _queryset = []
        if resource_type:
            for item in queryset:
                try:
                    if hasattr(item, resource_type):
                        _queryset.append(item)
                except Exception as e:
                    logger.debug(e)
        queryset = _queryset if _queryset else queryset
        yield from queryset

    def member_queryset(self):
        return self.groupmember_set.all()

    def get_members(self):
        """
        Returns a queryset of the group's members.
        """
        return get_user_model().objects.filter(
            Q(id__in=self.member_queryset().filter(role=GroupMember.MEMBER).values_list("user", flat=True))
        )

    def get_managers(self):
        """
        Returns a queryset of the group's managers.
        """
        return get_user_model().objects.filter(
            Q(id__in=self.member_queryset().filter(role=GroupMember.MANAGER).values_list("user", flat=True))
        )

    def user_is_member(self, user):
        if not user.is_authenticated:
            return False
        elif user.is_superuser:
            return True
        return user.id in self.member_queryset().values_list("user", flat=True)

    def user_is_role(self, user, role):
        if not user.is_authenticated:
            return False
        elif user.is_superuser:
            return True
        return self.member_queryset().filter(user=user, role=role).exists()

    def can_view(self, user):
        if user.is_superuser and user.is_authenticated:
            return True
        if self.access == "private":
            return user.is_authenticated and self.user_is_member(user)
        else:
            return True

    def validate_user(self, user):
        if not user or user.is_anonymous or user == user.get_anonymous():
            raise ValueError("The invited user cannot be anonymous")

    def join(self, user, **kwargs):
        self.validate_user(user)
        try:
            GroupMember.objects.get(group=self, user=user)
            logger.warning(f'The invited user "{user.username}" is already a member')
        except ObjectDoesNotExist:
            GroupMember.objects.create(group=self, user=user, **kwargs)

    def leave(self, user, **kwargs):
        self.validate_user(user)
        _members = GroupMember.objects.filter(group=self, user=user)
        if _members.exists():
            _members.delete()
            user.groups.remove(self.group)
        else:
            logger.warning(f'The invited user "{user.username}" is not a member')

    def promote(self, user, **kwargs):
        self.validate_user(user)
        try:
            _member = GroupMember.objects.get(group=self, user=user)
            _member.promote()
        except ObjectDoesNotExist:
            logger.warning(f'The invited user "{user.username}" is not a member')

    def demote(self, user, **kwargs):
        self.validate_user(user)
        try:
            _member = GroupMember.objects.get(group=self, user=user)
            _member.demote()
        except ObjectDoesNotExist:
            logger.warning(f'The invited user "{user.username}" is not a member')

    def get_absolute_url(self):
        return reverse(
            "group_detail",
            args=[
                self.slug,
            ],
        )

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def logo_url(self):
        _missing_thumbnail_url = static(MISSING_THUMB)
        try:
            _base_path = os.path.split(self.logo.path)[0]
            _upload_path = os.path.split(self.logo.url)[1]
            _upload_path = os.path.join(_base_path, _upload_path)
            if not os.path.exists(_upload_path):
                copyfile(self.logo.path, _upload_path)
        except Exception as e:
            logger.debug(e)
        _url = None
        try:
            _url = self.logo.url
        except Exception as e:
            logger.debug(e)
            return build_absolute_uri(_missing_thumbnail_url)
        return build_absolute_uri(_url)


class GroupMember(models.Model):
    MANAGER = "manager"
    MEMBER = "member"

    group = models.ForeignKey(GroupProfile, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10,
        choices=[
            (MANAGER, _("Manager")),
            (MEMBER, _("Member")),
        ],
    )
    joined = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        # add django.contrib.auth.group to user
        self.user.groups.add(self.group.group)
        super().save(*args, **kwargs)
        self._handle_perms(role=self.role)

    def delete(self, *args, **kwargs):
        self.user.groups.remove(self.group.group)
        super().delete(*args, **kwargs)
        self._handle_perms()

    def promote(self, *args, **kwargs):
        self.role = "manager"
        super().save(*args, **kwargs)
        self._handle_perms(role=self.role)

    def demote(self, *args, **kwargs):
        self.role = "member"
        super().save(*args, **kwargs)
        self._handle_perms(role=self.role)

    def _handle_perms(self, role=None):
        from geonode.security.utils import AdvancedSecurityWorkflowManager

        if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
            AdvancedSecurityWorkflowManager.set_group_member_permissions(self.user, self.group, role)


def group_pre_delete(instance, sender, **kwargs):
    """Make sure that the anonymous group is not deleted"""
    if instance.name == "anonymous":
        raise Exception(
            "Deletion of the anonymous group is\
         not permitted as will break the geonode permissions system"
        )


signals.pre_delete.connect(group_pre_delete, sender=Group)
