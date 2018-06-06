# -*- coding: utf-8 -*-
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.db.models import signals
from django.utils.timezone import now

from taggit.managers import TaggableManager
from guardian.shortcuts import get_objects_for_group


class GroupCategory(models.Model):
    slug = models.SlugField(max_length=255, unique=True, null=False, blank=False)
    name = models.CharField(_("Name"), max_length=255, unique=True, null=False, blank=False)
    description = models.TextField(_("Description"), null=True, default=None, blank=True)

    class Meta:
        verbose_name_plural = _('Group Categories')

    def __str__(self):
        return 'Category: {}'.format(self.name.encode('utf-8'))

    def get_absolute_url(self):
        return reverse('group_category_detail', args=(self.slug,))


def group_category_pre_save(sender, instance, *args, **kwargs):
    instance.slug = slugify(instance.name)


signals.pre_save.connect(group_category_pre_save, sender=GroupCategory)


class GroupProfile(models.Model):
    GROUP_CHOICES = [
        ("public", _("Public")),
        ("public-invite", _("Public (invite-only)")),
        ("private", _("Private")),
    ]

    access_help_text = _('Public: Any registered user can view and join a public group.<br>'
                         'Public (invite-only):Any registered user can view the group.  '
                         'Only invited users can join.<br>'
                         'Private: Registered users cannot see any details about the group, including membership.  '
                         'Only invited users can join.')
    email_help_text = _('Email used to contact one or all group members, '
                        'such as a mailing list, shared email, or exchange group.')

    group = models.OneToOneField(Group)
    title = models.CharField(_('Title'), max_length=50)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(_('Logo'), upload_to="people_group", blank=True)
    description = models.TextField(_('Description'))
    email = models.EmailField(
        _('Email'),
        null=True,
        blank=True,
        help_text=email_help_text)
    keywords = TaggableManager(
        _('Keywords'),
        help_text=_("A space or comma-separated list of keywords"),
        blank=True)
    access = models.CharField(
        _('Access'),
        max_length=15,
        default="public'",
        choices=GROUP_CHOICES,
        help_text=access_help_text)
    last_modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(GroupCategory, verbose_name=_("Categories"), blank=True, related_name='groups')
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        group, created = Group.objects.get_or_create(name=self.slug)
        self.group = group
        super(GroupProfile, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        Group.objects.filter(name=self.slug).delete()
        super(GroupProfile, self).delete(*args, **kwargs)

    @classmethod
    def groups_for_user(cls, user):
        """
        Returns the groups that user is a member of.  If the user is a superuser, all groups are returned.
        """
        if user.is_authenticated():
            if user.is_superuser:
                return cls.objects.all()
            return cls.objects.filter(groupmember__user=user)
        return []

    def __unicode__(self):
        return self.title

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
            self.group, [
                'base.view_resourcebase', 'base.change_resourcebase'], any_perm=True)

        if resource_type:
            queryset = [
                item for item in queryset if hasattr(
                    item,
                    resource_type)]

        for resource in queryset:
            yield resource

    def member_queryset(self):
        return self.groupmember_set.all()

    def get_managers(self):
        """
        Returns a queryset of the group's managers.
        """
        return get_user_model().objects.filter(
            id__in=self.member_queryset().filter(
                role='manager').values_list(
                "user",
                flat=True))

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

    def join(self, user, **kwargs):
        if user == user.get_anonymous():
            raise ValueError("The invited user cannot be anonymous")
        member, created = GroupMember.objects.get_or_create(group=self, user=user, defaults=kwargs)
        if created:
            user.groups.add(self.group)
        else:
            raise ValueError("The invited user \"{0}\" is already a member".format(user.username))

    @models.permalink
    def get_absolute_url(self):
        return ('group_detail', (), {'slug': self.slug})

    @property
    def class_name(self):
        return self.__class__.__name__


class GroupMember(models.Model):
    MANAGER = "manager"
    MEMBER = "member"

    group = models.ForeignKey(GroupProfile)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    role = models.CharField(max_length=10, choices=[
        (MANAGER, _("Manager")),
        (MEMBER, _("Member")),
    ])
    joined = models.DateTimeField(default=now)


def group_pre_delete(instance, sender, **kwargs):
    """Make sure that the anonymous group is not deleted"""
    if instance.name == 'anonymous':
        raise Exception('Deletion of the anonymous group is\
         not permitted as will break the geonode permissions system')


signals.pre_delete.connect(group_pre_delete, sender=Group)
