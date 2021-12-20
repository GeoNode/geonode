# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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
import json
import logging
import requests
import traceback
from lxml import etree
import xml.etree.ElementTree as ET
from defusedxml import lxml as dlxml

from requests.auth import HTTPBasicAuth

from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from guardian.utils import get_user_obj_perms_model
from guardian.shortcuts import (
    assign_perm,
    get_anonymous_user,
    get_objects_for_user)

from geonode import geoserver
from geonode.utils import get_layer_workspace
from geonode.decorators import on_ogc_backend
from geonode.groups.models import GroupProfile
from rest_framework import exceptions

logger = logging.getLogger("geonode.security.utils")


class GeofenceRequestError(exceptions.APIException):
    pass


class GeofenceLayerAdapter(object):
    def __init__(self, resource):
        self.resource = resource
        self.__has_committed_changes = False
        self.safe_point_rules = []

    @property
    def has_committed_changes(self):
        return self.__has_committed_changes

    def set_has_committed_changes(self):
        """
        Create save point before first commit
        """
        if not self.__has_committed_changes:
            self.__has_committed_changes = True
            self.safe_point_rules = self.list_rules(xml=True)

    def purge_rules(self):
        self.set_has_committed_changes()
        purge_geofence_layer_rules(self.resource)

    def list_rules(self, xml=False):
        layer = self.resource.layer
        workspace = get_layer_workspace(layer)
        layer_name = (
            layer.name
            if layer and hasattr(layer, 'name') else
            layer.alternate
        )
        if xml:
            rules = list_geofence_layer_rules_xml(workspace, layer_name)
            if not rules or len(rules) == 0:
                rules = list_geofence_layer_rules_xml(workspace, layer.alternate)
            return rules
        rules = list_geofence_layer_rules(workspace, layer_name)
        if not rules or len(rules) == 0:
            rules = list_geofence_layer_rules(workspace, layer.alternate)
        return rules

    def delete_rules(self, ids):
        self.set_has_committed_changes()
        batch_delete_geofence_layer_rules(ids)

    def update_rule(self, *args, **kwargs):
        self.set_has_committed_changes()
        _update_geofence_rule(*args, **kwargs)

    def restore_saved_rules(self, fail_silently):
        for rule in self.safe_point_rules:
            try:
                rule.attrib.pop("id")
                _create_geofence_rule(etree.tostring(rule))
            except GeofenceRequestError as exc:
                user = rule.find("userName").text
                layer_name = rule.find("layer").text
                msg = (
                    f"Could not ADD GeoServer User {user} Rule for "
                    f"Layer {layer_name}: '{exc.detail}'"
                )
                if 'Duplicate Rule' in exc.detail:
                    logger.debug(msg)
                elif not fail_silently:
                    raise

    def set_invalidate_cache(self):
        set_geofence_invalidate_cache()

    def toggle_layer_cache(self, *args, **kwags):
        toggle_layer_cache(*args, **kwags)

    def rollback(self):
        if self.has_committed_changes:
            try:
                self.set_invalidate_cache()
                self.purge_rules()
                self.restore_saved_rules(fail_silently=True)
                self.__has_committed_changes = False
                return True
            except Exception as e:
                logger.debug(e)
                return False
        else:
            return True


class GeofenceLayerRulesUnitOfWork(object):
    def __init__(self, geofence_adapter):
        self.adapter = geofence_adapter
        self.requests_list = []
        self.nested_contexts = 0
        self.adapter_requests_map = {
            "purge_rules": self.adapter.purge_rules,
            "delete_rules": self.adapter.delete_rules,
            "update_rule": self.adapter.update_rule,
            "set_invalidate_cache": self.adapter.set_invalidate_cache,
            "toggle_layer_cache": self.adapter.toggle_layer_cache,
        }

    def __enter__(self):
        self.nested_contexts += 1
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.nested_contexts -= 1
        if self.nested_contexts == 0:
            if not exc_type:
                self._execute_requests()
            else:
                self.rollback()

    def _execute_requests(self):
        for request in self.requests_list:
            self.adapter_requests_map[request["name"]](
                *request["args"], **request["kwargs"]
            )

    def rollback(self):
        self.adapter.rollback()
        self.requests_list = []

    def _add_request(self, request_details):
        self.requests_list.append(request_details)

    def purge_rules(self, *args, **kwargs):
        self._add_request(
            {
                "name": "purge_rules",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def delete_rules(self, *args, **kwargs):
        self._add_request(
            {
                "name": "delete_rules",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def update_rule(self, *args, **kwargs):
        self._add_request(
            {
                "name": "update_rule",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def set_invalidate_cache(self, *args, **kwargs):
        self._add_request(
            {
                "name": "set_invalidate_cache",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def toggle_layer_cache(self, *args, **kwargs):
        self._add_request(
            {
                "name": "toggle_layer_cache",
                "args": args,
                "kwargs": kwargs,
            }
        )


def get_visible_resources(queryset,
                          user,
                          request=None,
                          metadata_only=False,
                          admin_approval_required=False,
                          unpublished_not_visible=False,
                          private_groups_not_visibile=False):
    # Get the list of objects the user has access to
    is_admin = user.is_superuser if user and user.is_authenticated else False
    anonymous_group = None
    public_groups = GroupProfile.objects.exclude(access="private").values('group')
    groups = []
    group_list_all = []
    try:
        group_list_all = user.group_list_all().values('group')
    except Exception:
        pass

    try:
        anonymous_group = Group.objects.get(name='anonymous')
        if anonymous_group and anonymous_group not in groups:
            groups.append(anonymous_group)
    except Exception:
        pass

    # Hide Dirty State Resources
    filter_set = queryset.filter(
        Q(dirty_state=False) & Q(metadata_only=metadata_only))

    if not is_admin:
        if user:
            _allowed_resources = get_objects_for_user(user, 'base.view_resourcebase')
            filter_set = filter_set.filter(id__in=_allowed_resources.values('id'))

        if admin_approval_required:
            if not user or not user.is_authenticated or user.is_anonymous:
                filter_set = filter_set.filter(
                    Q(is_published=True) |
                    Q(group__in=public_groups) |
                    Q(group__in=groups)
                ).exclude(is_approved=False)

        # Hide Unpublished Resources to Anonymous Users
        if unpublished_not_visible:
            if not user or not user.is_authenticated or user.is_anonymous:
                filter_set = filter_set.exclude(is_published=False)

        # Hide Resources Belonging to Private Groups
        if private_groups_not_visibile:
            private_groups = GroupProfile.objects.filter(access="private").values('group')
            if user and user.is_authenticated:
                filter_set = filter_set.exclude(
                    Q(group__in=private_groups) & ~(
                        Q(owner__username__iexact=str(user)) | Q(group__in=group_list_all))
                )
            else:
                filter_set = filter_set.exclude(group__in=private_groups)

    return filter_set


def get_users_with_perms(obj):
    """
    Override of the Guardian get_users_with_perms
    """
    from .permissions import (VIEW_PERMISSIONS, ADMIN_PERMISSIONS, LAYER_ADMIN_PERMISSIONS, SERVICE_PERMISSIONS)
    ctype = ContentType.objects.get_for_model(obj)
    permissions = {}
    PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS + SERVICE_PERMISSIONS

    if str(ctype) == 'layer':
        for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
            permissions[perm.id] = perm.codename
    else:
        for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH):
            permissions[perm.id] = perm.codename

    user_model = get_user_obj_perms_model(obj)
    users_with_perms = user_model.objects.filter(object_pk=obj.pk,
                                                 permission_id__in=permissions).values('user_id', 'permission_id')

    users = {}
    for item in users_with_perms:
        if item['user_id'] in users:
            users[item['user_id']].append(permissions[item['permission_id']])
        else:
            users[item['user_id']] = [permissions[item['permission_id']], ]

    profiles = {}
    for profile in get_user_model().objects.filter(id__in=list(users.keys())):
        profiles[profile] = users[profile.id]

    return profiles


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def get_geofence_rules(page=0, entries=1, count=False):
    """Get the number of available GeoFence Cache Rules"""
    try:
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']

        _url = ''
        _headers = {'Content-type': 'application/json'}
        if count:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules/count.json
            """
            _url = f"{url}rest/geofence/rules/count.json"
        elif page or entries:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules.json?page={page}&entries={entries}
            """
            _url = f'{url}rest/geofence/rules.json?page={page}&entries={entries}'
        r = requests.get(_url,
                         headers=_headers,
                         auth=HTTPBasicAuth(user, passwd),
                         timeout=10,
                         verify=False)
        if (r.status_code < 200 or r.status_code > 201):
            logger.debug("Could not retrieve GeoFence Rules count.")

        rules_objs = json.loads(r.text)
        return rules_objs
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        return {'count': -1}


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def get_geofence_rules_count():
    """Get the number of available GeoFence Cache Rules"""
    rules_objs = get_geofence_rules(count=True)
    rules_count = rules_objs['count']
    return rules_count


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def get_highest_priority():
    """Get the highest Rules priority"""
    try:
        rules_count = get_geofence_rules_count()
        rules_objs = get_geofence_rules(rules_count - 1)
        if len(rules_objs['rules']) > 0:
            highest_priority = rules_objs['rules'][0]['priority']
        else:
            highest_priority = 0
        return int(highest_priority)
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        return -1


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def purge_geofence_all():
    """purge all existing GeoFence Cache Rules"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -X GET -u admin:geoserver -H "Content-Type: application/json" \
                  http://<host>:<port>/geoserver/rest/geofence/rules.json
            """
            headers = {'Content-type': 'application/json'}
            r = requests.get(f"{url}rest/geofence/rules.json",
                             headers=headers,
                             auth=HTTPBasicAuth(user, passwd),
                             timeout=10,
                             verify=False)
            if (r.status_code < 200 or r.status_code > 201):
                logger.debug("Could not Retrieve GeoFence Rules")
            else:
                try:
                    rules_objs = json.loads(r.text)
                    rules_count = rules_objs['count']
                    rules = rules_objs['rules']
                    if rules_count > 0:
                        # Delete GeoFence Rules associated to the Layer
                        # curl -X DELETE -u admin:geoserver http://<host>:<port>/geoserver/rest/geofence/rules/id/{r_id}
                        for rule in rules:
                            r = requests.delete(f"{url}rest/geofence/rules/id/{str(rule['id'])}",
                                                headers=headers,
                                                auth=HTTPBasicAuth(user, passwd))
                            if (r.status_code < 200 or r.status_code > 201):
                                msg = f"Could not DELETE GeoServer Rule id[{rule['id']}]"
                                e = Exception(msg)
                                logger.debug(f"Response [{r.status_code}] : {r.text}")
                                raise e
                except Exception:
                    logger.debug(f"Response [{r.status_code}] : {r.text}")
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def batch_delete_geofence_layer_rules(ids):
    """
    curl -X DELETE -u admin:geoserver http://<host>:<port>/geoserver/rest/geofence/rules/id/{r_id}
    """
    url = settings.OGC_SERVER["default"]["LOCATION"]
    user = settings.OGC_SERVER["default"]["USER"]
    passwd = settings.OGC_SERVER["default"]["PASSWORD"]
    headers = {"Content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)

    for rule_id in ids:
        resource_url = f"{url}rest/geofence/rules/id/{str(rule_id)}"
        response = requests.delete(resource_url, headers=headers, auth=auth)
        if response.status_code < 200 or response.status_code > 201:
            msg = f"Could not DELETE GeoServer Rule {str(rule_id)}"
            e = Exception(msg)
            logger.debug(f"Response [{response.status_code}] : {response.text}")
            raise e


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def list_geofence_layer_rules(workspace, layer_name):
    """
    curl -u admin:geoserver
    http://<host>:<port>/geoserver/rest/geofence/rules.json?workspace=geonode&layer={layer}
    """
    url = settings.OGC_SERVER["default"]["LOCATION"]
    user = settings.OGC_SERVER["default"]["USER"]
    passwd = settings.OGC_SERVER["default"]["PASSWORD"]
    headers = {"Content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)

    rules = []
    resource_url = f"{url}rest/geofence/rules.json?workspace={workspace}&layer={layer_name}"
    response = requests.get(resource_url, headers=headers, auth=auth, timeout=10, verify=False)
    if response.status_code >= 200 and response.status_code < 300:
        gs_rules = response.json()
        if gs_rules and gs_rules["rules"]:
            for rule in gs_rules["rules"]:
                if rule["layer"] and rule["layer"] == layer_name:
                    rules.append(rule)

    return rules


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def list_geofence_layer_rules_xml(workspace, layer_name):
    """
    curl -u admin:geoserver
    http://<host>:<port>/geoserver/rest/geofence/rules?workspace=geonode&layer={layer}
    """
    url = settings.OGC_SERVER["default"]["LOCATION"]
    user = settings.OGC_SERVER["default"]["USER"]
    passwd = settings.OGC_SERVER["default"]["PASSWORD"]
    headers = {"Content-type": "application/xml"}
    auth = HTTPBasicAuth(user, passwd)

    rules = []
    resource_url = f"{url}rest/geofence/rules?workspace={workspace}&layer={layer_name}"
    response = requests.get(resource_url, headers=headers, auth=auth, timeout=10, verify=False)
    if response.status_code >= 200 and response.status_code < 300:
        gs_rules = etree.fromstring(response.content)
        for rule in gs_rules:
            layer_field = rule.find("layer")
            if layer_field is not None and hasattr(layer_field, "text") and layer_field.text == layer_name:
                rules.append(rule)

    return rules


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def purge_geofence_layer_rules(resource):
    """purge layer existing GeoFence Cache Rules"""
    # Scan GeoFence Rules associated to the Layer
    """
    curl -u admin:geoserver
    http://<host>:<port>/geoserver/rest/geofence/rules.json?workspace=geonode&layer={layer}
    """
    layer = resource.layer
    workspace = get_layer_workspace(layer)
    layer_name = layer.name if layer and hasattr(layer, "name") else layer.alternate
    try:
        rules = list_geofence_layer_rules(workspace, layer_name)
        if not rules or len(rules) == 0:
            rules = list_geofence_layer_rules(workspace, layer.alternate)
        batch_delete_geofence_layer_rules([rule["id"] for rule in rules])
    except Exception as e:
        logger.exception(e)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geofence_invalidate_cache():
    """invalidate GeoFence Cache Rules"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -X GET -u admin:geoserver \
                  http://<host>:<port>/geoserver/rest/ruleCache/invalidate
            """
            r = requests.put(f"{url}rest/ruleCache/invalidate",
                             auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug("Could not Invalidate GeoFence Rules.")
                return False
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def toggle_layer_cache(layer_name, enable=True, filters=None, formats=None, geofence_uow=None):
    """Disable/enable a GeoServer Tiled Layer Configuration"""
    if geofence_uow:
        geofence_uow.toggle_layer_cache(
            layer_name, enable=enable, filters=filters, formats=formats
        )
        return True
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -v -u admin:geoserver -XGET \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.get(f'{url}gwc/rest/layers/{layer_name}.xml',
                             auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug(f"Could not Retrieve {layer_name} Cache.")
                return False
            try:
                xml_content = r.content
                tree = dlxml.fromstring(xml_content)

                gwc_id = tree.find('id')
                tree.remove(gwc_id)

                gwc_enabled = tree.find('enabled')
                if gwc_enabled is None:
                    gwc_enabled = etree.Element('enabled')
                    tree.append(gwc_enabled)
                gwc_enabled.text = str(enable).lower()

                gwc_mimeFormats = tree.find('mimeFormats')
                # Returns an element instance or None
                if gwc_mimeFormats is not None and len(gwc_mimeFormats):
                    tree.remove(gwc_mimeFormats)

                if formats is not None:
                    for format in formats:
                        gwc_format = etree.Element('string')
                        gwc_format.text = format
                        gwc_mimeFormats.append(gwc_format)

                    tree.append(gwc_mimeFormats)

                gwc_parameterFilters = tree.find('parameterFilters')
                if filters is None:
                    tree.remove(gwc_parameterFilters)
                else:
                    for filter in filters:
                        for k, v in filter.items():
                            """
                            <parameterFilters>
                                <styleParameterFilter>
                                    <key>STYLES</key>
                                    <defaultValue/>
                                </styleParameterFilter>
                            </parameterFilters>
                            """
                            gwc_parameter = etree.Element(k)
                            for parameter_key, parameter_value in v.items():
                                gwc_parameter_key = etree.Element('key')
                                gwc_parameter_key.text = parameter_key
                                gwc_parameter_value = etree.Element('defaultValue')
                                gwc_parameter_value.text = parameter_value

                                gwc_parameter.append(gwc_parameter_key)
                                gwc_parameter.append(gwc_parameter_value)
                            gwc_parameterFilters.append(gwc_parameter)

                """
                curl -v -u admin:geoserver -XPOST \
                    -H "Content-type: text/xml" -d @poi.xml \
                        "http://localhost:8080/geoserver/gwc/rest/layers/tiger:poi.xml"
                """
                headers = {'Content-type': 'text/xml'}
                payload = ET.tostring(tree)
                r = requests.post(f'{url}gwc/rest/layers/{layer_name}.xml',
                                  headers=headers,
                                  data=payload,
                                  auth=HTTPBasicAuth(user, passwd))
                if (r.status_code < 200 or r.status_code > 201):
                    logger.debug(f"Could not Update {layer_name} Cache.")
                    return False
            except Exception:
                tb = traceback.format_exc()
                logger.debug(tb)
                return False
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def delete_layer_cache(layer_name):
    """Delete a GeoServer Tiled Layer Configuration and all the cache"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -v -u admin:geoserver -XDELETE \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.delete(f'{url}gwc/rest/layers/{layer_name}.xml',
                                auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug(f"Could not Delete {layer_name} Cache.")
                return False
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geowebcache_invalidate_cache(layer_alternate, cat=None):
    """invalidate GeoWebCache Cache Rules"""
    if layer_alternate is not None and len(layer_alternate) and "None" not in layer_alternate:
        try:
            if cat is None or cat.get_layer(layer_alternate) is not None:
                url = settings.OGC_SERVER['default']['LOCATION']
                user = settings.OGC_SERVER['default']['USER']
                passwd = settings.OGC_SERVER['default']['PASSWORD']
                """
                curl -v -u admin:geoserver \
                -H "Content-type: text/xml" \
                -d "<truncateLayer><layerName>{layer_alternate}</layerName></truncateLayer>" \
                http://localhost:8080/geoserver/gwc/rest/masstruncate
                """
                headers = {'Content-type': 'text/xml'}
                payload = f"<truncateLayer><layerName>{layer_alternate}</layerName></truncateLayer>"
                r = requests.post(
                    f"{url}gwc/rest/masstruncate",
                    headers=headers,
                    data=payload,
                    auth=HTTPBasicAuth(user, passwd))
                if (r.status_code < 200 or r.status_code > 201):
                    logger.debug(f"Could not Truncate GWC Cache for Layer '{layer_alternate}'.")
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)


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
    logger.debug(f"Inside set_geofence_all for instance {instance}")
    workspace = get_layer_workspace(resource.layer)
    layer_name = resource.layer.name if resource.layer and hasattr(resource.layer, 'name') \
        else resource.layer.alternate
    logger.debug(f"going to work in workspace {workspace}")
    try:
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']

        # Create GeoFence Rules for ANONYMOUS to the Layer
        """
        curl -X POST -u admin:geoserver -H "Content-Type: text/xml" -d \
        "<Rule><workspace>geonode</workspace><layer>{layer}</layer><access>ALLOW</access></Rule>" \
        http://<host>:<port>/geoserver/rest/geofence/rules
        """
        headers = {'Content-type': 'application/xml'}
        payload = _get_geofence_payload(
            layer_name=layer_name,
            workspace=workspace,
            access="ALLOW"
        )
        response = requests.post(
            f"{url}rest/geofence/rules",
            headers=headers,
            data=payload,
            auth=HTTPBasicAuth(user, passwd)
        )
        if response.status_code not in (200, 201):
            logger.debug(
                f"Response {response.status_code} : {response.text}")
            raise RuntimeError("Could not ADD GeoServer ANONYMOUS Rule "
                               f"for Layer {layer_name}")
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
    finally:
        if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
            set_geofence_invalidate_cache()
        else:
            resource.set_dirty_state()


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def sync_geofence_with_guardian(layer, perms, user=None, group=None, group_perms=None, geofence_uow=None):
    """
    Sync Guardian permissions to GeoFence.
    """
    _layer_name = layer.name if layer and hasattr(layer, 'name') else layer.alternate
    _layer_workspace = get_layer_workspace(layer)
    # Create new rule-set
    gf_services = _get_gf_services(layer, perms)

    gf_requests = {}
    if 'change_layer_data' not in perms:
        _skip_perm = False
        if user and group_perms:
            if isinstance(user, str):
                user = get_user_model().objects.get(username=user)
            user_groups = list(user.groups.all().values_list('name', flat=True))
            for _group, _perm in group_perms.items():
                if 'change_layer_data' in _perm and _group in user_groups:
                    _skip_perm = True
                    break
        if not _skip_perm:
            gf_requests["WFS"] = {
                "TRANSACTION": False,
                "LOCKFEATURE": False,
                "GETFEATUREWITHLOCK": False
            }
    _user = None
    _group = None
    users_geolimits = None
    groups_geolimits = None
    anonymous_geolimits = None

    _group, _user, _disable_cache, users_geolimits, groups_geolimits, anonymous_geolimits = get_user_geolimits(layer, user, group, gf_services)

    if _disable_cache:
        # Re-order dictionary
        # - if geo-limits have been defined for this user/group, the "*" rule must be the first one
        gf_services_limits_first = {"*": gf_services.pop('*')}
        gf_services_limits_first.update(gf_services)
        gf_services = gf_services_limits_first

    for service, allowed in gf_services.items():
        if layer and _layer_name and allowed:
            if _user:
                logger.debug(f"Adding 'user' to geofence the rule: {layer} {service} {_user}")
                _wkt = None
                if users_geolimits and users_geolimits.count():
                    _wkt = users_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, user=_user, allow=enabled, geofence_uow=geofence_uow)
                _update_geofence_rule(_layer_name, _layer_workspace, service, user=_user, geo_limit=_wkt, geofence_uow=geofence_uow)
            elif not _group:
                logger.debug(f"Adding to geofence the rule: {layer} {service} *")
                _wkt = None
                if anonymous_geolimits and anonymous_geolimits.count():
                    _wkt = anonymous_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, user=_user, allow=enabled, geofence_uow=geofence_uow)
                _update_geofence_rule(_layer_name, _layer_workspace, service, geo_limit=_wkt, geofence_uow=geofence_uow)
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, user=_user, allow=enabled, geofence_uow=geofence_uow)
            if _group:
                logger.debug(f"Adding 'group' to geofence the rule: {layer} {service} {_group}")
                _wkt = None
                if groups_geolimits and groups_geolimits.count():
                    _wkt = groups_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, group=_group, allow=enabled, geofence_uow=geofence_uow)
                _update_geofence_rule(_layer_name, _layer_workspace, service, group=_group, geo_limit=_wkt, geofence_uow=geofence_uow)
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, group=_group, allow=enabled, geofence_uow=geofence_uow)

    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        if geofence_uow:
            geofence_uow.set_invalidate_cache()
        else:
            set_geofence_invalidate_cache()
    else:
        layer.set_dirty_state()


def get_user_geolimits(layer, user, group, gf_services):
    _user = None
    _group = None
    users_geolimits = None
    groups_geolimits = None
    anonymous_geolimits = None
    _disable_layer_cache = False
    if user:
        _user = user if isinstance(user, str) else user.username
        users_geolimits = layer.users_geolimits.filter(user=get_user_model().objects.get(username=_user))
        gf_services["*"] = users_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
        _disable_layer_cache = users_geolimits.count() > 0

    if group:
        _group = group if isinstance(group, str) else group.name
        if GroupProfile.objects.filter(group__name=_group).count() == 1:
            groups_geolimits = layer.groups_geolimits.filter(group=GroupProfile.objects.get(group__name=_group))
            gf_services["*"] = groups_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
            _disable_layer_cache = groups_geolimits.count() > 0

    if not user and not group:
        anonymous_geolimits = layer.users_geolimits.filter(user=get_anonymous_user())
        gf_services["*"] = anonymous_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
        _disable_layer_cache = anonymous_geolimits.count() > 0
    return _group, _user, _disable_layer_cache, users_geolimits, groups_geolimits, anonymous_geolimits


def _get_gf_services(layer, perms):
    gf_services = {}
    gf_services["WMS"] = 'view_resourcebase' in perms or 'change_layer_style' in perms
    gf_services["GWC"] = 'view_resourcebase' in perms or 'change_layer_style' in perms
    gf_services["WFS"] = ('download_resourcebase' in perms or 'change_layer_data' in perms) \
        and layer.is_vector()
    gf_services["WCS"] = ('download_resourcebase' in perms or 'change_layer_data' in perms) \
        and not layer.is_vector()
    gf_services["WPS"] = 'download_resourcebase' in perms or 'change_layer_data' in perms
    gf_services["*"] = 'download_resourcebase' in perms and \
        ('view_resourcebase' in perms or 'change_layer_style' in perms)

    return gf_services


def set_owner_permissions(resource, members=None):
    """assign all admin permissions to the owner"""
    from .permissions import (VIEW_PERMISSIONS, ADMIN_PERMISSIONS, LAYER_ADMIN_PERMISSIONS, SERVICE_PERMISSIONS)
    if resource.polymorphic_ctype:
        # Owner & Manager Admin Perms
        admin_perms = VIEW_PERMISSIONS + ADMIN_PERMISSIONS
        for perm in admin_perms:
            if not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS:
                assign_perm(perm, resource.owner, resource.get_self_resource())
            elif perm not in {'change_resourcebase_permissions', 'publish_resourcebase'}:
                assign_perm(perm, resource.owner, resource.get_self_resource())
            if members:
                for user in members:
                    assign_perm(perm, user, resource.get_self_resource())

        # Set the GeoFence Owner Rule
        if resource.polymorphic_ctype.name == 'layer':
            for perm in LAYER_ADMIN_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.layer)
                if members:
                    for user in members:
                        assign_perm(perm, user, resource.layer)

        if resource.polymorphic_ctype.name == 'service':
            for perm in SERVICE_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.service)
                if members:
                    for user in members:
                        assign_perm(perm, user, resource.service)


def remove_object_permissions(instance, purge=True, geofence_uow=None):
    """Remove object permissions on given resource.

    If is a layer removes the layer specific permissions then the
    resourcebase permissions

    """
    from guardian.models import UserObjectPermission, GroupObjectPermission
    resource = instance.get_self_resource()
    try:
        if hasattr(resource, "layer"):
            UserObjectPermission.objects.filter(
                content_type=ContentType.objects.get_for_model(resource.layer),
                object_pk=instance.id
            ).delete()
            GroupObjectPermission.objects.filter(
                content_type=ContentType.objects.get_for_model(resource.layer),
                object_pk=instance.id
            ).delete()
    except (ObjectDoesNotExist, RuntimeError):
        pass  # This layer is not manageable by geofence
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
    finally:
        if purge:
            if instance.polymorphic_ctype.name == 'layer':
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
                        if geofence_uow:
                            geofence_uow.purge_rules()
                            geofence_uow.set_invalidate_cache()
                        else:
                            purge_geofence_layer_rules(resource)
                            set_geofence_invalidate_cache()
                    else:
                        resource.set_dirty_state()
    UserObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                        object_pk=instance.id).delete()
    GroupObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                         object_pk=instance.id).delete()


def _get_geofence_payload(layer_name, workspace, access, user=None, group=None,
                          service=None, request=None, geo_limit=None):
    highest_priority = get_highest_priority()
    root_el = etree.Element("Rule")
    username_el = etree.SubElement(root_el, "userName")
    if user is not None:
        username_el.text = user
    else:
        username_el.text = ''
    priority_el = etree.SubElement(root_el, "priority")
    priority_el.text = str(highest_priority if highest_priority >= 0 else 0)
    if group is not None:
        role_el = etree.SubElement(root_el, "roleName")
        role_el.text = f"ROLE_{group.upper()}"
    workspace_el = etree.SubElement(root_el, "workspace")
    workspace_el.text = workspace
    layer_el = etree.SubElement(root_el, "layer")
    layer_el.text = layer_name
    if service is not None and service != "*":
        service_el = etree.SubElement(root_el, "service")
        service_el.text = service
    if request is not None and request != "*":
        service_el = etree.SubElement(root_el, "request")
        service_el.text = request
    if service and service == "*" and geo_limit is not None and geo_limit != "":
        access_el = etree.SubElement(root_el, "access")
        access_el.text = "LIMIT"
        limits = etree.SubElement(root_el, "limits")
        catalog_mode = etree.SubElement(limits, "catalogMode")
        catalog_mode.text = "MIXED"
        allowed_area = etree.SubElement(limits, "allowedArea")
        allowed_area.text = geo_limit
    else:
        access_el = etree.SubElement(root_el, "access")
        access_el.text = access
    return etree.tostring(root_el)


def _create_geofence_rule(payload):
    username = settings.OGC_SERVER['default']['USER']
    password = settings.OGC_SERVER['default']['PASSWORD']
    url = settings.OGC_SERVER['default']['LOCATION']
    headers = {'Content-type': 'application/xml'}
    auth = HTTPBasicAuth(username=username, password=password)

    logger.debug(f"request data: {payload}")
    resource_url = f"{url}rest/geofence/rules"
    response = requests.post(
        resource_url,
        data=payload,
        headers=headers,
        auth=auth
    )
    logger.debug(f"response status_code: {response.status_code}")
    if response.status_code not in (200, 201):
        raise GeofenceRequestError(detail=response.text)


def _update_geofence_rule(layer_name, workspace,
                          service, request=None,
                          user=None, group=None,
                          geo_limit=None, allow=True,
                          geofence_uow=None):
    if geofence_uow:
        geofence_uow.update_rule(
            layer_name, workspace, service,
            request=request, user=user, group=group,
            geo_limit=geo_limit, allow=allow
        )
        return None
    payload = _get_geofence_payload(
        layer_name=layer_name,
        workspace=workspace,
        access="ALLOW" if allow else "DENY",
        user=user,
        group=group,
        service=service,
        request=request,
        geo_limit=geo_limit
    )
    try:
        _create_geofence_rule(payload)
    except GeofenceRequestError as exc:
        msg = (
            f"Could not ADD GeoServer User {user} Rule for "
            f"Layer {layer_name}: '{exc.detail}'"
        )
        if 'Duplicate Rule' in exc.detail:
            logger.debug(msg)
        else:
            raise RuntimeError(msg)


def sync_resources_with_guardian(resource=None):
    """
    Sync resources with Guardian and clear their dirty state
    """

    from geonode.base.models import ResourceBase
    from geonode.layers.models import Layer

    if resource:
        dirty_resources = ResourceBase.objects.filter(id=resource.id)
    else:
        dirty_resources = ResourceBase.objects.filter(dirty_state=True)
    if dirty_resources and dirty_resources.count() > 0:
        logger.debug(" --------------------------- synching with guardian!")
        for r in dirty_resources:
            if r.polymorphic_ctype.name == 'layer':
                layer = None
                try:
                    purge_geofence_layer_rules(r)
                    layer = Layer.objects.get(id=r.id)
                    perm_spec = layer.get_all_level_info()
                    # All the other users
                    if 'users' in perm_spec:
                        for user, perms in perm_spec['users'].items():
                            user = get_user_model().objects.get(username=user)
                            # Set the GeoFence User Rules
                            geofence_user = str(user)
                            if "AnonymousUser" in geofence_user or get_anonymous_user() in geofence_user:
                                geofence_user = None
                            sync_geofence_with_guardian(layer, perms, user=geofence_user)
                    # All the other groups
                    if 'groups' in perm_spec:
                        for group, perms in perm_spec['groups'].items():
                            group = Group.objects.get(name=group)
                            # Set the GeoFence Group Rules
                            sync_geofence_with_guardian(layer, perms, group=group)
                    r.clear_dirty_state()
                except Exception as e:
                    logger.exception(e)
                    logger.warn(f"!WARNING! - Failure Synching-up Security Rules for Resource [{r}]")


def get_resources_with_perms(user, filter_options={}, shortcut_kwargs={}):
    """
    Returns resources a user has access to.
    """

    from geonode.base.models import ResourceBase

    if settings.SKIP_PERMS_FILTER:
        resources = ResourceBase.objects.all()
    else:
        resources = get_objects_for_user(
            user,
            'base.view_resourcebase',
            **shortcut_kwargs
        )

    resources_with_perms = get_visible_resources(
        resources,
        user,
        admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
        unpublished_not_visible=settings.RESOURCE_PUBLISHING,
        private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

    if filter_options:
        if resources_with_perms and resources_with_perms.count() > 0:
            if filter_options.get('title_filter'):
                resources_with_perms = resources_with_perms.filter(
                    title__icontains=filter_options.get('title_filter')
                )
            type_filters = []
            if filter_options.get('type_filter'):
                _type_filter = filter_options.get('type_filter')
                if _type_filter:
                    type_filters.append(_type_filter)
                # get subtypes for geoapps
                if _type_filter == 'geoapp':
                    type_filters.extend(get_geoapp_subtypes())

            if type_filters:
                resources_with_perms = resources_with_perms.filter(
                    polymorphic_ctype__model__in=type_filters
                )

    return resources_with_perms


def get_geoapp_subtypes():
    """
    Returns a list of geoapp subtypes.
    eg ['geostory']
    """

    from geonode.geoapps.models import GeoApp

    subtypes = []
    for label, app in apps.app_configs.items():
        if hasattr(app, 'type') and app.type == 'GEONODE_APP':
            if hasattr(app, 'default_model'):
                _model = apps.get_model(label, app.default_model)
                if issubclass(_model, GeoApp):
                    subtypes.append(_model.__name__.lower())
    return subtypes


def skip_registered_members_common_group(user_group):
    from geonode.groups.conf import settings as groups_settings
    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
        _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
        if (settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS) and \
                _members_group_name == user_group.name:
            return True
    return False
