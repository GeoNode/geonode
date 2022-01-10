#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import typing
import requests
import traceback
import xml.etree.ElementTree as ET

from lxml import etree
from defusedxml import lxml as dlxml
from requests.auth import HTTPBasicAuth
from guardian.shortcuts import get_anonymous_user

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from geonode.utils import get_dataset_workspace
from geonode.groups.models import GroupProfile

logger = logging.getLogger(__name__)


def _get_geofence_payload(layer, dataset_name, workspace, access, user=None, group=None,
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
    dataset_el = etree.SubElement(root_el, "layer")
    dataset_el.text = dataset_name
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


def _update_geofence_rule(layer, dataset_name, workspace,
                          service, request=None,
                          user=None, group=None,
                          geo_limit=None, allow=True):
    payload = _get_geofence_payload(
        layer=layer,
        dataset_name=dataset_name,
        workspace=workspace,
        access="ALLOW" if allow else "DENY",
        user=user,
        group=group,
        service=service,
        request=request,
        geo_limit=geo_limit
    )
    logger.debug(f"request data: {payload}")
    response = requests.post(
        f"{settings.OGC_SERVER['default']['LOCATION']}rest/geofence/rules",
        data=payload,
        headers={
            'Content-type': 'application/xml'
        },
        auth=HTTPBasicAuth(
            username=settings.OGC_SERVER['default']['USER'],
            password=settings.OGC_SERVER['default']['PASSWORD']
        )
    )
    logger.debug(f"response status_code: {response.status_code}")
    if response.status_code not in (200, 201):
        msg = (f"Could not ADD GeoServer User {user} Rule for "
               f"Dataset {layer}: '{response.text}'")
        if 'Duplicate Rule' in response.text:
            logger.debug(msg)
        else:
            raise RuntimeError(msg)


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


def get_geofence_rules_count():
    """Get the number of available GeoFence Cache Rules"""
    rules_objs = get_geofence_rules(count=True)
    rules_count = rules_objs['count']
    return rules_count


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
                        # Delete GeoFence Rules associated to the Dataset
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


def purge_geofence_dataset_rules(resource):
    """purge layer existing GeoFence Cache Rules"""
    # Scan GeoFence Rules associated to the Dataset
    """
    curl -u admin:geoserver
    http://<host>:<port>/geoserver/rest/geofence/rules.json?workspace=geonode&layer={layer}
    """
    url = settings.OGC_SERVER['default']['LOCATION']
    user = settings.OGC_SERVER['default']['USER']
    passwd = settings.OGC_SERVER['default']['PASSWORD']
    headers = {'Content-type': 'application/json'}
    workspace = get_dataset_workspace(resource.dataset)
    dataset_name = resource.dataset.name if resource.dataset and hasattr(resource.dataset, 'name') \
        else resource.dataset.alternate
    try:
        r = requests.get(
            f"{url}rest/geofence/rules.json?workspace={workspace}&layer={dataset_name}",
            headers=headers,
            auth=HTTPBasicAuth(user, passwd),
            timeout=10,
            verify=False
        )
        if (r.status_code >= 200 and r.status_code < 300):
            gs_rules = r.json()
            r_ids = []
            if gs_rules and gs_rules['rules']:
                for r in gs_rules['rules']:
                    if r['layer'] and r['layer'] == dataset_name:
                        r_ids.append(r['id'])

            # Delete GeoFence Rules associated to the Dataset
            # curl -X DELETE -u admin:geoserver http://<host>:<port>/geoserver/rest/geofence/rules/id/{r_id}
            for r_id in r_ids:
                r = requests.delete(
                    f"{url}rest/geofence/rules/id/{str(r_id)}",
                    headers=headers,
                    auth=HTTPBasicAuth(user, passwd))
                if (r.status_code < 200 or r.status_code > 201):
                    msg = "Could not DELETE GeoServer Rule for Dataset "
                    msg = msg + str(dataset_name)
                    e = Exception(msg)
                    logger.debug(f"Response [{r.status_code}] : {r.text}")
                    logger.exception(e)
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)


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


def toggle_dataset_cache(dataset_name, enable=True, filters=None, formats=None):
    """Disable/enable a GeoServer Tiled Dataset Configuration"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -v -u admin:geoserver -XGET \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.get(f'{url}gwc/rest/layers/{dataset_name}.xml',
                             auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug(f"Could not Retrieve {dataset_name} Cache.")
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
                r = requests.post(f'{url}gwc/rest/layers/{dataset_name}.xml',
                                  headers=headers,
                                  data=payload,
                                  auth=HTTPBasicAuth(user, passwd))
                if (r.status_code < 200 or r.status_code > 201):
                    logger.debug(f"Could not Update {dataset_name} Cache.")
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


def delete_dataset_cache(dataset_name):
    """Delete a GeoServer Tiled Dataset Configuration and all the cache"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -v -u admin:geoserver -XDELETE \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.delete(f'{url}gwc/rest/layers/{dataset_name}.xml',
                                auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug(f"Could not Delete {dataset_name} Cache.")
                return False
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


def set_geowebcache_invalidate_cache(dataset_alternate, cat=None):
    """invalidate GeoWebCache Cache Rules"""
    if dataset_alternate is not None and len(dataset_alternate) and "None" not in dataset_alternate:
        try:
            if cat is None or cat.get_layer(dataset_alternate) is not None:
                url = settings.OGC_SERVER['default']['LOCATION']
                user = settings.OGC_SERVER['default']['USER']
                passwd = settings.OGC_SERVER['default']['PASSWORD']
                """
                curl -v -u admin:geoserver \
                -H "Content-type: text/xml" \
                -d "<truncateLayer><layerName>{dataset_alternate}</layerName></truncateLayer>" \
                http://localhost:8080/geoserver/gwc/rest/masstruncate
                """
                headers = {'Content-type': 'text/xml'}
                payload = f"<truncateLayer><layerName>{dataset_alternate}</layerName></truncateLayer>"
                r = requests.post(
                    f"{url}gwc/rest/masstruncate",
                    headers=headers,
                    data=payload,
                    auth=HTTPBasicAuth(user, passwd))
                if (r.status_code < 200 or r.status_code > 201):
                    logger.debug(f"Could not Truncate GWC Cache for Dataset '{dataset_alternate}'.")
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)


def set_geofence_all(instance):
    """assign access permissions to all users

    This method is only relevant to Dataset instances that have their
    underlying data managed by geoserver, meaning:

    * layers that are not associated with a Service
    * layers that are associated with a Service that is being CASCADED through
      geoserver

    """

    resource = instance.get_self_resource()
    logger.debug(f"Inside set_geofence_all for instance {instance}")
    workspace = get_dataset_workspace(resource.dataset)
    dataset_name = resource.dataset.name if resource.dataset and hasattr(resource.dataset, 'name') \
        else resource.dataset.alternate
    logger.debug(f"going to work in workspace {workspace}")
    try:
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']

        # Create GeoFence Rules for ANONYMOUS to the Dataset
        """
        curl -X POST -u admin:geoserver -H "Content-Type: text/xml" -d \
        "<Rule><workspace>geonode</workspace><layer>{layer}</layer><access>ALLOW</access></Rule>" \
        http://<host>:<port>/geoserver/rest/geofence/rules
        """
        headers = {'Content-type': 'application/xml'}
        payload = _get_geofence_payload(
            layer=resource.dataset,
            dataset_name=dataset_name,
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
                               f"for Dataset {dataset_name}")
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
    finally:
        if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
            set_geofence_invalidate_cache()
        else:
            resource.set_dirty_state()


def sync_geofence_with_guardian(dataset, perms, user=None, group=None, group_perms=None):
    """
    Sync Guardian permissions to GeoFence.
    """
    _dataset_name = dataset.name if dataset and hasattr(dataset, 'name') else dataset.alternate
    _dataset_workspace = get_dataset_workspace(dataset)
    # Create new rule-set
    gf_services = _get_gf_services(dataset, perms)

    gf_requests = {}
    if 'change_dataset_data' not in perms:
        _skip_perm = False
        if user and group_perms:
            if isinstance(user, str):
                user = get_user_model().objects.get(username=user)
            user_groups = list(user.groups.all().values_list('name', flat=True))
            for _group, _perm in group_perms.items():
                if 'change_dataset_data' in _perm and _group in user_groups:
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
    _group, _user, _disable_cache, users_geolimits, groups_geolimits, anonymous_geolimits = get_user_geolimits(dataset, user, group, gf_services)

    if _disable_cache:
        gf_services_limits_first = {"*": gf_services.pop('*')}
        gf_services_limits_first.update(gf_services)
        gf_services = gf_services_limits_first

    for service, allowed in gf_services.items():
        if dataset and _dataset_name and allowed:
            if _user:
                logger.debug(f"Adding 'user' to geofence the rule: {dataset} {service} {_user}")
                _wkt = None
                if users_geolimits and users_geolimits.count():
                    _wkt = users_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(dataset, _dataset_name, _dataset_workspace,
                                              service, request=request, user=_user, allow=enabled)
                _update_geofence_rule(dataset, _dataset_name, _dataset_workspace, service, user=_user, geo_limit=_wkt)
            elif not _group:
                logger.debug(f"Adding to geofence the rule: {dataset} {service} *")
                _wkt = None
                if anonymous_geolimits and anonymous_geolimits.count():
                    _wkt = anonymous_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(dataset, _dataset_name, _dataset_workspace,
                                              service, request=request, user=_user, allow=enabled)
                _update_geofence_rule(dataset, _dataset_name, _dataset_workspace, service, geo_limit=_wkt)
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(dataset, _dataset_name, _dataset_workspace,
                                              service, request=request, user=_user, allow=enabled)
            if _group:
                logger.debug(f"Adding 'group' to geofence the rule: {dataset} {service} {_group}")
                _wkt = None
                if groups_geolimits and groups_geolimits.count():
                    _wkt = groups_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(dataset, _dataset_name, _dataset_workspace,
                                              service, request=request, group=_group, allow=enabled)
                _update_geofence_rule(dataset, _dataset_name, _dataset_workspace, service, group=_group, geo_limit=_wkt)
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(dataset, _dataset_name, _dataset_workspace,
                                              service, request=request, group=_group, allow=enabled)
    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        set_geofence_invalidate_cache()
    else:
        dataset.set_dirty_state()


def sync_resources_with_guardian(resource=None):
    """
    Sync resources with Guardian and clear their dirty state
    """
    from geonode.layers.models import Dataset
    from geonode.base.models import ResourceBase

    if resource:
        dirty_resources = ResourceBase.objects.filter(id=resource.id)
    else:
        dirty_resources = ResourceBase.objects.filter(dirty_state=True)
    if dirty_resources and dirty_resources.count() > 0:
        logger.debug(" --------------------------- synching with guardian!")
        for r in dirty_resources:
            if r.polymorphic_ctype.name == 'dataset':
                layer = None
                try:
                    purge_geofence_dataset_rules(r)
                    layer = Dataset.objects.get(id=r.id)
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


def get_user_geolimits(layer, user, group, gf_services):
    _user = None
    _group = None
    _disable_dataset_cache = None
    users_geolimits = None
    groups_geolimits = None
    anonymous_geolimits = None
    if user:
        _user = user if isinstance(user, str) else user.username
        users_geolimits = layer.users_geolimits.filter(user=get_user_model().objects.get(username=_user))
        gf_services["*"] = users_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
        _disable_dataset_cache = users_geolimits.count() > 0

    if group:
        _group = group if isinstance(group, str) else group.name
        if GroupProfile.objects.filter(group__name=_group).count() == 1:
            groups_geolimits = layer.groups_geolimits.filter(group=GroupProfile.objects.get(group__name=_group))
            gf_services["*"] = groups_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
            _disable_dataset_cache = groups_geolimits.count() > 0

    if not user and not group:
        anonymous_geolimits = layer.users_geolimits.filter(user=get_anonymous_user())
        gf_services["*"] = anonymous_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
        _disable_dataset_cache = anonymous_geolimits.count() > 0
    return _group, _user, _disable_dataset_cache, users_geolimits, groups_geolimits, anonymous_geolimits


def _get_gf_services(layer, perms):
    gf_services = {}
    gf_services["WMS"] = 'view_resourcebase' in perms or 'change_dataset_style' in perms
    gf_services["GWC"] = 'view_resourcebase' in perms or 'change_dataset_style' in perms
    gf_services["WFS"] = ('download_resourcebase' in perms or 'change_dataset_data' in perms) \
        and layer.is_vector()
    gf_services["WCS"] = ('download_resourcebase' in perms or 'change_dataset_data' in perms) \
        and not layer.is_vector()
    gf_services["WPS"] = 'download_resourcebase' in perms or 'change_dataset_data' in perms
    gf_services["*"] = 'download_resourcebase' in perms and \
        ('view_resourcebase' in perms or 'change_dataset_style' in perms)

    return gf_services


def _get_gwc_filters_and_formats(disable_cache: list = []) -> typing.Tuple[list, list]:
    filters = [{
        "styleParameterFilter": {
            "STYLES": ""
        }
    }]
    formats = [
        'application/json;type=utfgrid',
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/png8',
        'image/vnd.jpeg-png',
        'image/vnd.jpeg-png8'
    ]
    if disable_cache and any(disable_cache):
        filters = None
        formats = None
    return (filters, formats)
