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
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import signals

from geonode.base.models import ResourceBase
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.people.models import Profile


class SiteResources(models.Model):
    """Relations to link the resources to the sites"""
    site = models.OneToOneField(Site)
    resources = models.ManyToManyField(ResourceBase, blank=True, null=True)

    def __unicode__(self):
        return self.site.name

    class Meta:
        verbose_name_plural = 'Site Resources'


class SitePeople(models.Model):
    """Relations to link the people to the sites"""
    site = models.OneToOneField(Site)
    people = models.ManyToManyField(Profile, blank=True, null=True)

    def __unicode__(self):
        return self.site.name

    class Meta:
        verbose_name_plural = 'Site People'


class SiteGroups(models.Model):
    """Relations to link the groups to the sites"""
    site = models.OneToOneField(Site)
    groups = models.ManyToManyField(GroupProfile, blank=True)

    def __unicode__(self):
        return self.site.name

    class Meta:
        verbose_name_plural = 'Site Groups'


def post_save_resource(instance, sender, **kwargs):
    """Signal to ensure that every created resource is
    assigned to the current site and to the master site"""
    current_site = Site.objects.get_current()
    SiteResources.objects.get(site=current_site).resources.add(instance.get_self_resource())
    if current_site.id != 1:
        SiteResources.objects.get(site_id=1).resources.add(instance.get_self_resource())


def post_save_site(instance, sender, **kwargs):
    """Signal to create the SiteResources on site save"""
    SiteResources.objects.get_or_create(site=instance)
    SitePeople.objects.get_or_create(site=instance)
    SiteGroups.objects.get_or_create(site=instance)


def post_delete_resource(instance, sender, **kwargs):
    """Signal to ensure that on resource delete it get remove from the SiteResources as well"""
    current_site = Site.objects.get_current()
    SiteResources.objects.get(site=current_site).resources.remove(instance.get_self_resource())
    if current_site.id != 1:
        SiteResources.objects.get(site_id=1).resources.remove(instance.get_self_resource())


def post_delete_site(instance, sender, **kwargs):
    """Signal to delete the SiteResources on site delete"""
    SiteResources.objects.filter(site=instance).delete()
    SitePeople.objects.filter(site=instance).delete()


def post_save_profile(instance, sender, created, **kwargs):
    """Signal to ensure that every created user is
    assigned to the current site only"""
    if not instance.is_superuser and created and not kwargs['raw'] and instance.username != 'AnonymousUser':
        current_site = Site.objects.get_current()
        SitePeople.objects.get(site=current_site).people.add(instance)


def post_delete_profile(instance, sender, **kwargs):
    """Signal to delete the SitePeople on profile delete"""
    if not instance.is_superuser:
        current_site = Site.objects.get_current()
        SitePeople.objects.get(site=current_site).people.remove(instance)


def post_save_group(instance, sender, **kwargs):
    """Signal to ensure that every created group is
    assigned to the current site only"""
    if kwargs['created'] and not kwargs['raw']:
        current_site = Site.objects.get_current()
        SiteGroups.objects.get(site=current_site).groups.add(instance)


def post_delete_group(instance, sender, **kwargs):
    """Signal to delete the SitePeople on profile delete"""
    current_site = Site.objects.get_current()
    SiteGroups.objects.get(site=current_site).groups.remove(instance)


# Django doesn't propagate the signals to the parents so we need to add the listeners on the children
if 'geonode.contrib.geosites' in settings.INSTALLED_APPS:
    signals.post_save.connect(post_save_resource, sender=Layer)
    signals.post_save.connect(post_save_resource, sender=Map)
    signals.post_save.connect(post_save_resource, sender=Document)
    signals.post_save.connect(post_save_site, sender=Site)
    signals.post_delete.connect(post_delete_resource, sender=Layer)
    signals.post_delete.connect(post_delete_resource, sender=Map)
    signals.post_delete.connect(post_delete_resource, sender=Document)
    signals.post_delete.connect(post_delete_site, sender=Site)
    signals.post_save.connect(post_save_profile, sender=Profile)
    signals.post_delete.connect(post_delete_profile, sender=Profile)
    signals.post_save.connect(post_save_group, sender=GroupProfile)
    signals.post_delete.connect(post_delete_group, sender=GroupProfile)
