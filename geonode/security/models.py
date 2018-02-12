# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
from geonode import geoserver
from geonode.decorators import on_ogc_backend
from lxml import etree

try:
    import json
except ImportError:
    from django.utils import simplejson as json
import logging
import traceback
import requests

from requests.auth import HTTPBasicAuth

from django.contrib.auth import get_user_model

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import login
from django.contrib.auth.models import Group, Permission
from geonode.groups.models import GroupProfile
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from guardian.utils import get_user_obj_perms_model
from guardian.shortcuts import assign_perm, get_groups_with_perms

from ..services.enumerations import CASCADED

logger = logging.getLogger("geonode.security.models")

ADMIN_PERMISSIONS = [
    'view_resourcebase',
    'download_resourcebase',
    'change_resourcebase_metadata',
    'change_resourcebase',
    'delete_resourcebase',
    'change_resourcebase_permissions',
    'publish_resourcebase',
]

LAYER_ADMIN_PERMISSIONS = [
    'change_layer_data',
    'change_layer_style'
]

GEOFENCE_SECURITY_ENABLED = settings.OGC_SERVER['default'].get(
    "GEOFENCE_SECURITY_ENABLED", False)


def get_users_with_perms(obj):
    """
    Override of the Guardian get_users_with_perms
    """
    ctype = ContentType.objects.get_for_model(obj)
    permissions = {}
    PERMISSIONS_TO_FETCH = ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS

    for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
        permissions[perm.id] = perm.codename

    user_model = get_user_obj_perms_model(obj)
    users_with_perms = user_model.objects.filter(object_pk=obj.pk,
                                                 content_type_id=ctype.id,
                                                 permission_id__in=permissions).values('user_id', 'permission_id')

    users = {}
    for item in users_with_perms:
        if item['user_id'] in users:
            users[item['user_id']].append(permissions[item['permission_id']])
        else:
            users[item['user_id']] = [permissions[item['permission_id']], ]

    profiles = {}
    for profile in get_user_model().objects.filter(id__in=users.keys()):
        profiles[profile] = users[profile.id]

    return profiles


class PermissionLevelError(Exception):
    pass


class PermissionLevelMixin(object):

    """
    Mixin for adding "Permission Level" methods
    to a model class -- eg role systems where a
    user has exactly one assigned role with respect to
    an object representing an "access level"
    """

    def get_all_level_info(self):

        resource = self.get_self_resource()
        users = get_users_with_perms(resource)
        groups = get_groups_with_perms(resource,
                                       attach_perms=True)
        if groups:
            for group in groups:
                try:
                    group_profile = GroupProfile.objects.get(slug=group.name)
                    managers = group_profile.get_managers()
                    if managers:
                        for manager in managers:
                            if manager not in users and not manager.is_superuser:
                                for perm in ADMIN_PERMISSIONS:
                                    assign_perm(perm, manager, resource)
                                users[manager] = ADMIN_PERMISSIONS
                except GroupProfile.DoesNotExist:
                    pass
        info = {
            'users': users,
            'groups': groups}

        # TODO very hugly here, but isn't huglier
        # to set layer permissions to resource base?
        if hasattr(self, "layer"):
            info_layer = {
                'users': get_users_with_perms(
                    self.layer),
                'groups': get_groups_with_perms(
                    self.layer,
                    attach_perms=True)}

            for user in info_layer['users']:
                if user in info['users']:
                    info['users'][user] = info['users'][user] + info_layer['users'][user]
                else:
                    info['users'][user] = info_layer['users'][user]

            for group in info_layer['groups']:
                if group in info['groups']:
                    info['groups'][group] = info['groups'][group] + info_layer['groups'][group]
                else:
                    info['groups'][group] = info_layer['groups'][group]

        return info

    def get_self_resource(self):
        return self.resourcebase_ptr if hasattr(
            self,
            'resourcebase_ptr_id') else self

    def set_default_permissions(self):
        """
        Remove all the permissions except for the owner and assign the
        view permission to the anonymous group
        """
        remove_object_permissions(self)

        # default permissions for anonymous users
        anonymous_group, created = Group.objects.get_or_create(name='anonymous')

        if not anonymous_group:
            raise Exception("Could not acquire 'anonymous' Group.")

        # default permissions for resource owner
        set_owner_permissions(self)

        anonymous_can_view = settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION
        if anonymous_can_view:
            assign_perm('view_resourcebase',
                        anonymous_group, self.get_self_resource())

        if self.__class__.__name__ == 'Layer':
            if anonymous_can_view and GEOFENCE_SECURITY_ENABLED:
                set_geofence_all(self)
            # only for layer owner
            assign_perm('change_layer_data', self.owner, self)
            assign_perm('change_layer_style', self.owner, self)

        if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
            assign_perm('download_resourcebase',
                        anonymous_group, self.get_self_resource())

    def set_permissions(self, perm_spec):
        """
        Sets an object's the permission levels based on the perm_spec JSON.


        the mapping looks like:
        {
            'users': {
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            }
            'groups': [
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
                ]
        }
        """

        remove_object_permissions(self)

        # default permissions for resource owner
        set_owner_permissions(self)

        if 'users' in perm_spec and "AnonymousUser" in perm_spec['users']:
            anonymous_group = Group.objects.get(name='anonymous')
            for perm in perm_spec['users']['AnonymousUser']:
                if self.polymorphic_ctype.name == 'layer' and perm in ('change_layer_data', 'change_layer_style',
                                                                       'add_layer', 'change_layer', 'delete_layer',):
                    assign_perm(perm, anonymous_group, self.layer)
                else:
                    assign_perm(perm, anonymous_group, self.get_self_resource())

        if 'users' in perm_spec:
            for user, perms in perm_spec['users'].items():
                user = get_user_model().objects.get(username=user)
                # Set the GeoFence Owner Rules
                has_view_perms = ('view_resourcebase' in perms)
                has_download_perms = ('download_resourcebase' in perms)
                geofence_user = str(user)
                if "AnonymousUser" in geofence_user:
                    geofence_user = None
                if GEOFENCE_SECURITY_ENABLED:
                    set_geofence_owner(self, username=geofence_user,
                                       view_perms=has_view_perms,
                                       download_perms=has_download_perms)

                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, user, self.layer)
                    else:
                        assign_perm(perm, user, self.get_self_resource())

        if 'groups' in perm_spec:
            for group, perms in perm_spec['groups'].items():
                group = Group.objects.get(name=group)
                # Set the GeoFence Owner Rules
                has_view_perms = ('view_resourcebase' in perms)
                has_download_perms = ('download_resourcebase' in perms)
                if GEOFENCE_SECURITY_ENABLED:
                    set_geofence_group(
                        self, str(group),
                        view_perms=has_view_perms,
                        download_perms=has_download_perms
                    )

                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, group, self.layer)
                    else:
                        assign_perm(perm, group, self.get_self_resource())


def get_geofence_rules_count():
    """invalidate GeoFence Cache Rules"""
    try:
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']
        # Check first that the rules does not exist already
        """
        curl -X GET -u admin:geoserver \
              http://<host>:<port>/geoserver/geofence/rest/rules/count.json
        """
        headers = {'Content-type': 'application/json'}
        r = requests.get(url + 'geofence/rest/rules/count.json',
                         headers=headers,
                         auth=HTTPBasicAuth(user, passwd))
        if (r.status_code < 200 or r.status_code > 201):
            logger.warning("Could not retrieve GeoFence Rules count.")

        rules_objs = json.loads(r.text)
        rules_count = rules_objs['count']
        return int(rules_count)
    except:
        tb = traceback.format_exc()
        logger.debug(tb)
        return -1


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geofence_invalidate_cache():
    """invalidate GeoFence Cache Rules"""
    if GEOFENCE_SECURITY_ENABLED:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            # Check first that the rules does not exist already
            """
            curl -X GET -u admin:geoserver \
                  http://<host>:<port>/geoserver/rest/ruleCache/invalidate
            """
            r = requests.put(url + 'rest/ruleCache/invalidate',
                             auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.warning("Could not Invalidate GeoFence Rules.")
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            raise


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geofence_all(instance):
    """assign access permissions to all users

    This method is only relevant to Layer instances that have their
    underlying data managed by geoserver, meaning:

    * layers that are not associated with a Service
    * layers that are associated with a Service that is being CASCADED through
      geoserver

    """

    resource = instance.get_self_resource()
    logger.debug("Inside set_geofence_all for instance {}".format(instance))
    try:
        workspace = _get_layer_workspace(resource.layer)
        logger.debug("going to work in workspace {!r}".format(workspace))
    except (ObjectDoesNotExist, AttributeError, RuntimeError):
        # This is either not a layer (if raised AttributeError) or it is
        # a layer that is not manageable by geofence (if raised
        # RuntimeError) so we have nothing to do
        return
    try:
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']
        # Check first that the rules does not exist already
        """
        curl -X GET -u admin:geoserver -H "Content-Type: application/json" \
              http://<host>:<port>/geoserver/geofence/rest/rules.json?layer=<layer_name>
        """
        headers = {'Content-type': 'application/json'}
        r = requests.get(url + 'geofence/rest/rules.json?layer=' + resource.layer.name,
                         headers=headers,
                         auth=HTTPBasicAuth(user, passwd))

        rules_already_present = False
        if (r.status_code < 200 or r.status_code > 201):
            logger.warning("Could not GET GeoServer Rules for Layer " + str(resource.layer.name))
        else:
            try:
                rules_objs = json.loads(r.text)
                rules_count = rules_objs['count']
                rules = rules_objs['rules']
                if rules_count > 1:
                    for rule in rules:
                        if rule['userName'] is None and rule['access'] == 'ALLOW':
                            rules_already_present = True
            except Exception:
                logger.debug("Response [{}] : {}".format(r.status_code, r.text))
                raise

        # Create GeoFence Rules for ANONYMOUS to the Layer
        """
        curl -X POST -u admin:geoserver -H "Content-Type: text/xml" -d \
        "<Rule><workspace>geonode</workspace><layer>{layer}</layer><access>ALLOW</access></Rule>" \
        http://<host>:<port>/geoserver/geofence/rest/rules
        """
        rules_count = get_geofence_rules_count()
        headers = {'Content-type': 'application/xml'}
        payload = _get_geofence_payload(
            layer=resource.layer.name,
            workspace=workspace,
            access="ALLOW"
        )

        if not rules_already_present:
            response = requests.post(
                url + 'geofence/rest/rules',
                headers=headers,
                data=payload,
                auth=HTTPBasicAuth(user, passwd)
            )
            if response.status_code not in (200, 201):
                logger.debug(
                    "Response {!r} : {}".format(r.status_code, r.text))
                raise RuntimeError("Could not ADD GeoServer ANONYMOUS Rule "
                                   "for Layer {}".format(resource.layer.name))
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        raise
    finally:
        set_geofence_invalidate_cache()


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geofence_owner(instance, username=None, view_perms=False, download_perms=False):
    """Assign access permissions to owner user

    This function uses the geoserver REST API in order to contact geofence.
    The request performs a similar function to the one in the following cURL
    snippet:

        curl -X POST -u {admin_user}:{admin_password} \
          -H "Content-Type: text/xml" \
          -d "<Rule><userName>{user}</userName><workspace>geonode</workspace> \
          <layer>{layer}</layer><access>ALLOW</access></Rule>" \
          http://<host>:<port>/geoserver/geofence/rest/rules

    """

    resource = instance.get_self_resource()
    try:
        workspace = _get_layer_workspace(resource.layer)
    except (ObjectDoesNotExist, AttributeError, RuntimeError):
        # resource is either not a layer (if raised AttributeError) or
        # a layer that is not manageable by geofence (if raised
        # RuntimeError) so we have nothing to do
        pass
    else:
        services = (
            (["WMS", "GWC"] if view_perms else []) +
            (["WFS", "WCS", "WPS"] if download_perms else [])
        )
        try:
            for service in services:
                _update_geofence_rule(
                    layer=resource.layer.name,
                    workspace=workspace,
                    service=service,
                    user=username
                )
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            raise
        finally:
            set_geofence_invalidate_cache()


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geofence_group(instance, groupname, view_perms=False,
                       download_perms=False):
    """assign access permissions to owner group"""
    resource = instance.get_self_resource()
    try:
        workspace = _get_layer_workspace(resource.layer)
    except (ObjectDoesNotExist, AttributeError, RuntimeError):
        # resource is either not a layer (if raised AttributeError) or
        # a layer that is not manageable by geofence (if raised
        # RuntimeError) so we have nothing to do
        pass
    else:
        if groupname:
            services = (
                (["WMS", "GWC"] if view_perms else []) +
                (["WFS", "WCS", "WPS"] if download_perms else [])
            )
            try:
                for service in services:
                    _update_geofence_rule(
                        layer=resource.layer.name,
                        workspace=workspace,
                        group=groupname,
                        service=service
                    )
            except Exception:
                tb = traceback.format_exc()
                logger.debug(tb)
                raise
            finally:
                set_geofence_invalidate_cache()


def set_owner_permissions(resource):
    """assign all admin permissions to the owner"""
    if resource.polymorphic_ctype:
        # Set the GeoFence Owner Rule
        if resource.polymorphic_ctype.name == 'layer':
            # Assign GeoFence Layer Access to Owner
            geofence_user = str(resource.owner)
            if "AnonymousUser" in geofence_user:
                geofence_user = None
            if GEOFENCE_SECURITY_ENABLED:
                set_geofence_owner(resource, username=geofence_user)
            for perm in LAYER_ADMIN_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.layer)

        for perm in ADMIN_PERMISSIONS:
            assign_perm(perm, resource.owner, resource.get_self_resource())


def remove_object_permissions(instance):
    """Remove object permissions on given resource.

    If is a layer removes the layer specific permissions then the
    resourcebase permissions

    """

    from guardian.models import UserObjectPermission, GroupObjectPermission
    resource = instance.get_self_resource()
    if hasattr(resource, "layer"):
        try:
            UserObjectPermission.objects.filter(
                content_type=ContentType.objects.get_for_model(resource.layer),
                object_pk=instance.id
            ).delete()
            GroupObjectPermission.objects.filter(
                content_type=ContentType.objects.get_for_model(resource.layer),
                object_pk=instance.id
            ).delete()
            if GEOFENCE_SECURITY_ENABLED:
                # Scan GeoFence Rules associated to the Layer
                """
                curl -u admin:geoserver
                http://<host>:<port>/geoserver/geofence/rest/rules.json?workspace=geonode&layer={layer}
                """
                url = settings.OGC_SERVER['default']['LOCATION']
                user = settings.OGC_SERVER['default']['USER']
                passwd = settings.OGC_SERVER['default']['PASSWORD']
                headers = {'Content-type': 'application/json'}
                workspace = _get_layer_workspace(resource.layer)
                r = requests.get(
                    "{}geofence/rest/rules.json?workspace={}&layer={}".format(
                        url, workspace, resource.layer.name),
                    headers=headers,
                    auth=HTTPBasicAuth(user, passwd)
                )
                if (r.status_code >= 200):
                    gs_rules = r.json()
                    r_ids = []
                    if gs_rules and gs_rules['rules']:
                        for r in gs_rules['rules']:
                            if r['layer'] and r['layer'] == resource.layer.name:
                                r_ids.append(r['id'])

                    # Delete GeoFence Rules associated to the Layer
                    # curl -X DELETE -u admin:geoserver http://<host>:<port>/geoserver/geofence/rest/rules/id/{r_id}
                    for i, r_id in enumerate(r_ids):
                        r = requests.delete(url + 'geofence/rest/rules/id/' + str(r_id),
                                            headers=headers,
                                            auth=HTTPBasicAuth(user, passwd))
                        if (r.status_code < 200 or r.status_code > 201):
                            msg = "Could not DELETE GeoServer Rule for Layer "
                            msg = msg + str(resource.layer.name)
                            e = Exception(msg)
                            logger.debug("Response [{}] : {}".format(r.status_code, r.text))
                            raise e
        except (ObjectDoesNotExist, RuntimeError):
            pass  # This layer is not manageable by geofence
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            raise
        finally:
            set_geofence_invalidate_cache()

    UserObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                        object_pk=instance.id).delete()
    GroupObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                         object_pk=instance.id).delete()


# Logic to login a user automatically when it has successfully
# activated an account:
def autologin(sender, **kwargs):
    user = kwargs['user']
    request = kwargs['request']
    # Manually setting the default user backed to avoid the
    # 'User' object has no attribute 'backend' error
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    # This login function does not need password.
    login(request, user)

# FIXME(Ariel): Replace this signal with the one from django-user-accounts
# user_activated.connect(autologin)


def _get_layer_workspace(layer):
    """Get the workspace where the input layer belongs"""
    default_workspace = getattr(settings, "DEFAULT_WORKSPACE", "geonode")
    try:
        if layer.service.method == CASCADED:
            workspace = getattr(
                settings, "CASCADE_WORKSPACE", default_workspace)
        else:
            raise RuntimeError("Layer is not cascaded")
    except AttributeError:  # layer does not have a service
        workspace = default_workspace
    return workspace


def _get_geofence_payload(layer, workspace, access, user=None, group=None,
                          service=None):
    rules_count = get_geofence_rules_count()
    root_el = etree.Element("Rule")
    if user is not None:
        username_el = etree.SubElement(root_el, "userName")
        username_el.text = user
    priority_el = etree.SubElement(root_el, "priority")
    priority_el.text = str(rules_count - 1)
    if group is not None:
        role_el = etree.SubElement(root_el, "roleName")
        role_el.text = "ROLE_{}".format(group.upper())
    workspace_el = etree.SubElement(root_el, "workspace")
    workspace_el.text = workspace
    layer_el = etree.SubElement(root_el, "layer")
    layer_el.text = layer
    access_el = etree.SubElement(root_el, "access")
    access_el.text = access
    if service is not None:
        service_el = etree.SubElement(root_el, "service")
        service_el.text = service
    return etree.tostring(root_el)


def _update_geofence_rule(layer, workspace, service, user=None, group=None):
    payload = _get_geofence_payload(
        layer=layer,
        workspace=workspace,
        access="ALLOW",
        user=user,
        group=group,
        service=service
    )
    logger.debug("request data: {}".format(payload))
    response = requests.post(
        "{base_url}geofence/rest/rules".format(
            base_url=settings.OGC_SERVER['default']['LOCATION']),
        data=payload,
        headers={
            'Content-type': 'application/xml'
        },
        auth=HTTPBasicAuth(
            username=settings.OGC_SERVER['default']['USER'],
            password=settings.OGC_SERVER['default']['PASSWORD']
        )
    )
    if response.status_code not in (200, 201):
        msg = ("Could not ADD GeoServer User {!r} Rule for "
               "Layer {!r}".format(user, layer))
        raise RuntimeError(msg)
