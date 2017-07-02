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
try:
    import json
except ImportError:
    from django.utils import simplejson as json
import logging
import traceback
import requests
from urlparse import urlparse, parse_qsl
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib import urlencode
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import login
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from guardian.utils import get_user_obj_perms_model
from guardian.shortcuts import assign_perm, get_groups_with_perms
from xmltodict import parse

try:
    geofence_url = settings.GEOFENCE['url'].strip('/')
except AttributeError:
    geofence_url = "{}/geofence".format(settings.OGC_SERVER['default']['LOCATION'].strip('/'))

try:
    geofence_username = settings.GEOFENCE['username']
except AttributeError:
    geofence_username = settings.OGC_SERVER['default']['USER']

try:
    geofence_password = settings.GEOFENCE['password']
except AttributeError:
    geofence_password = settings.OGC_SERVER['default']['PASSWORD']

internal_geofence = settings.OGC_SERVER['default']['LOCATION'] in geofence_url
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

http_client = requests.session()
http_client.verify = True
parsed_url = urlparse(geofence_url)
retry = Retry(
    total=4,
    status=4,
    backoff_factor=0.9,
    status_forcelist=[502, 503, 504],
    method_whitelist=set(['HEAD', 'TRACE', 'GET', 'PUT', 'POST', 'OPTIONS', 'DELETE'])
)

http_client.mount("{}://".format(parsed_url.scheme), HTTPAdapter(max_retries=retry))


def http_request(url, data=None, method='get', headers={}, access_token=None):
    req_method = getattr(http_client, method.lower())
    resp = None

    if access_token:
        headers['Authorization'] = "Bearer {}".format(access_token)
        parsed_url = urlparse(url)
        params = parse_qsl(parsed_url.query.strip())
        params.append(('access_token', access_token))
        params = urlencode(params)
        url = "{proto}://{address}{path}?{params}".format(proto=parsed_url.scheme, address=parsed_url.netloc,
                                                          path=parsed_url.path, params=params)

        try:
            resp = req_method(url, headers=headers, data=data)
        except:
            logger.debug(traceback.format_exc())
    else:
        try:
            resp = req_method(url, headers=headers, data=data, auth=(geofence_username, geofence_password))
        except:
            logger.debug(traceback.format_exc())

    return resp


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
        info = {
            'users': get_users_with_perms(
                resource),
            'groups': get_groups_with_perms(
                resource,
                attach_perms=True)}

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

        set_geofence_permissions = False
        if settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION:
            assign_perm('view_resourcebase', anonymous_group, self.get_self_resource())
            set_geofence_permissions = True

        if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
            assign_perm('download_resourcebase', anonymous_group, self.get_self_resource())
            set_geofence_permissions = True

        # Give public access to all Geoserver layers
        if set_geofence_permissions:
            set_data_public_access(self)

        # default permissions for resource owner
        set_owner_permissions(self)

        # only for layer owner
        if self.__class__.__name__ == 'Layer':
            assign_perm('change_layer_data', self.owner, self)
            assign_perm('change_layer_style', self.owner, self)

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

        public_access = False
        if 'users' in perm_spec and "AnonymousUser" in perm_spec['users']:
            anonymous_group = Group.objects.get(name='anonymous')
            for perm in perm_spec['users']['AnonymousUser']:
                if self.polymorphic_ctype.name == 'layer' and perm in ('change_layer_data', 'change_layer_style',
                                                                       'add_layer', 'change_layer', 'delete_layer',):
                    assign_perm(perm, anonymous_group, self.layer)
                else:
                    assign_perm(perm, anonymous_group, self.get_self_resource())

                # Assign GeoFence Layer Access to unauthenticated users
                public_access = True
        if public_access:
            # if we allow public access to the layer, why also assign user specific permissions?
            set_data_public_access(self)
            # return

        # TODO refactor code here
        if 'users' in perm_spec:
            for user, perms in perm_spec['users'].items():
                user = get_user_model().objects.get(username=user)
                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, user, self.layer)
                    else:
                        assign_perm(perm, user, self.get_self_resource())
                # Set the GeoFence Owner Rules
                has_view_perms = ('view_resourcebase' in perms)
                has_edit_perms = ('change_layer_data' in perms)
                if user.username.lower() != 'anonymoususer':
                    # Anonymous access is already given above
                    set_data_acl(self, str(user), view_perms=has_view_perms, edit_perms=has_edit_perms)

        if 'groups' in perm_spec:
            for group, perms in perm_spec['groups'].items():
                group = Group.objects.get(name=group)
                for perm in perms:
                    if self.polymorphic_ctype.name == 'layer' and perm in (
                            'change_layer_data', 'change_layer_style',
                            'add_layer', 'change_layer', 'delete_layer',):
                        assign_perm(perm, group, self.layer)
                    else:
                        assign_perm(perm, group, self.get_self_resource())
                # Set the GeoFence Owner Rules
                has_view_perms = ('view_resourcebase' in perms)
                has_edit_perms = ('change_layer_data' in perms)
                if group.name.lower() != 'anonymous':
                    # Anonymous access is already given above
                    set_data_acl(self, str(group), view_perms=has_view_perms, edit_perms=has_edit_perms, type='group')

        # default permissions for resource owner
        set_owner_permissions(self)


def set_data_public_access(instance):
    """This will provide unauthenticated access to all services on the layer, which includes WFS-T"""
    resource = instance.get_self_resource()

    if hasattr(resource, "layer"):
        if internal_geofence:
            payload = "<Rule><workspace>{}</workspace>".format(resource.layer.workspace)
            payload += "<layer>{}</layer><access>ALLOW</access></Rule>".format(resource.layer.name)
        else:
            payload = "<rule grant='ALLOW'><position value='0' position='offsetFromTop'/>"
            payload += "<workspace>{}</workspace>".format(resource.layer.workspace)
            payload += "<layer>{}</layer></rule>".format(resource.layer.name)

        create_geofence_rule(payload)


def set_data_acl(instance, name, view_perms=False, edit_perms=False, type='user'):
    """assign access permissions to a user account"""
    resource = instance.get_self_resource()

    if hasattr(resource, "layer"):
        if internal_geofence:
            if type == 'user':
                payload = "<Rule><userName>{}</userName>".format(name)
            elif type == 'group':
                payload = "<Rule><roleName>ROLE_{}</roleName>".format(name.upper())
            payload += "<workspace>{}</workspace>".format(resource.layer.workspace)
            payload += "<layer>{}</layer><access>ALLOW</access>".format(resource.layer.name)
            rule_end = "</Rule>"
        else:
            payload = "<rule grant='ALLOW'><position value='0' position='offsetFromTop'/>"
            payload += "<workspace>{}</workspace>".format(resource.layer.workspace)
            payload += "<layer>{}</layer>".format(resource.layer.name)

            if type == 'user':
                payload += "<username>{}</username>".format(name)
            elif type == 'group':
                payload += "<rolename>ROLE_{}</rolename>".format(name.upper())
            rule_end = "</rule>"

        if view_perms and edit_perms:
            data = "{}{}".format(payload, rule_end)
            create_geofence_rule(rule=data)
        else:
            if view_perms:
                for service in ['WMS', 'GWC', 'WCS']:
                    data = "{}<service>{}</service>{}".format(payload, service, rule_end)
                    create_geofence_rule(rule=data)

                for type in ['GETCAPABILITIES', 'GETFEATURETYPE', 'DESCRIBEFEATURETYPE', 'GETFEATURE', 'GETGMLOBJECT']:
                    data = "{}<service>WFS</service><request>{}</request>{}".format(payload, type, rule_end)
                    create_geofence_rule(rule=data)

            if edit_perms:
                for service in ['WMS', 'GWC', 'WCS', 'WFS', 'WPS']:
                    data = "{}<service>{}</service>{}".format(payload, service, rule_end)
                    create_geofence_rule(rule=data)


def set_owner_permissions(resource):
    """assign all admin permissions to the owner"""
    if resource.polymorphic_ctype:
        if resource.polymorphic_ctype.name == 'layer':
            # Assign GeoFence Layer Access to Owner
            for perm in LAYER_ADMIN_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.layer)

        # Set the GeoFence Owner Rule
        set_data_acl(resource, str(resource.owner), view_perms=True, edit_perms=True)

        for perm in ADMIN_PERMISSIONS:
            assign_perm(perm, resource.owner, resource.get_self_resource())


def remove_object_permissions(instance):
    """Remove object perimssions on give resource.
        If is a layer removes the layer specific permissions then the resourcebase permissions
    """
    from guardian.models import UserObjectPermission, GroupObjectPermission
    resource = instance.get_self_resource()

    if hasattr(resource, "layer"):
        gs_rules = get_geofence_rules(workspace=resource.layer.workspace, layer=resource.layer.name)
        if gs_rules:
            gs_rules_dict = parse(gs_rules)
            if internal_geofence:
                key = 'Rules'
                sub_key = 'Rule'
            else:
                key = 'RuleList'
                sub_key = 'rule'

            # There are plenty of differences between the standalone and integrated versions of. Try dealing with them.
            if gs_rules_dict[key]:
                if sub_key in gs_rules_dict[key].keys():
                    rules = gs_rules_dict[key][sub_key]
                else:
                    rules = []
                if not isinstance(rules, list):
                    rules = [rules]
                for rule in rules:
                    if 'layer' in rule.keys() and rule['layer'] == resource.layer.name:
                        if '@id' in rule.keys():
                            delete_geofence_rule(rule['@id'])
                        else:
                            delete_geofence_rule(rule['id'])

        try:
            UserObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource.layer),
                                                object_pk=instance.id).delete()
        except:
            logger.debug(traceback.format_exc())

        try:
            GroupObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource.layer),
                                                 object_pk=instance.id).delete()
        except:
            logger.debug(traceback.format_exc())

        try:
            UserObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                                object_pk=instance.id).delete()
        except:
            logger.debug(traceback.format_exc())

        try:
            GroupObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                                 object_pk=instance.id).delete()
        except:
            logger.debug(traceback.format_exc())


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


def create_geofence_rule(rule=None):
    # Create GeoFence User's specific Access Limits
    """
    curl -X POST -u admin:geoserver -H "Content-Type: text/xml" -d \
    "<Rule><userName>{user}</userName><workspace>geonode</workspace> \
    <layer>{layer}</layer><access>ALLOW</access></Rule>" \
    http://<host>:<port>/geoserver/geofence/rest/rules
    """

    if rule:
        rules_url = "{}/rest/rules".format(geofence_url)
        headers = {'Content-type': 'application/xml'}
        geofence_rule = None

        resp = http_request(
            rules_url,
            method='post',
            headers=headers,
            data=rule
        )

        if resp.status_code in (200, 201):
            rule_id = resp.content
            geofence_rule = get_geofence_rule_by_id(id=rule_id)
            if not geofence_rule:
                logger.error("GeoFence created rule {}, however rule can not be found in GeoFence".format(rule_id))
        else:
            logger.error("Failed to add GeoFence rule {}".format(rule))

        return geofence_rule


def get_geofence_rule_by_id(id, output_type='xml'):
    """
    Get a single GeoFence rule by it's ID, either in json or xml format
    """

    rules_url = "{}/rest/rules".format(geofence_url)
    output_type = output_type.lower().strip('.')

    if id:
        if internal_geofence:
            id_url = "{}/id/{}.{}".format(rules_url, id, output_type)
        else:
            id_url = "{}/id/{}".format(rules_url, id)
        resp = http_request(id_url)

        if resp.status_code == 200:
            if output_type == 'json':
                return resp.json()
            else:
                return resp.content
        else:
            logger.warning("Could not find rule {} in GeoFence".format(id))
    return None


def get_geofence_rules(workspace=None, layer=None, output_type='xml'):
    """
    Get GeoFence rules, either in json or xml format. May provide a workspace/layername filter
    """

    rules_url = "{}/rest/rules".format(geofence_url)
    output_type = output_type.lower().strip('.')
    if internal_geofence:
        rules_url = "{}.{}".format(rules_url, output_type)

    params = {}

    if workspace:
        params['workspace'] = workspace
    if layer:
        params['layer'] = layer

    encode_params = urlencode(params)
    filter_url = "{}?{}".format(rules_url, encode_params)

    resp = http_request(filter_url)

    if resp.status_code == 200:
        if output_type == 'json':
            return resp.json()
        else:
            return resp.content
    else:
        logger.warning("Could not get rule from GeoFence")
    return None


def delete_geofence_rule(id):
    """
    Delete a GeoFence rule by rule ID
    """
    rule_url = "{}/rest/rules/id/{}".format(geofence_url, id)
    headers = {'Content-type': 'application/json'}
    resp = http_request(
        rule_url,
        method='delete',
        headers=headers
    )

    if resp.status_code == 200:
        return True
    else:
        logger.warning("Could not delete rule from GeoFence {}".format(id))
    return None
