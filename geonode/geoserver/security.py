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

from geonode.geoserver.geofence import GeofenceClient, Batch, Rule, AutoPriorityBatch
from geonode.utils import get_dataset_workspace
from geonode.groups.models import GroupProfile

logger = logging.getLogger(__name__)


def create_geofence_client():
    url = settings.OGC_SERVER['default']['LOCATION']
    user = settings.OGC_SERVER['default']['USER']
    passwd = settings.OGC_SERVER['default']['PASSWORD']

    client = GeofenceClient(url, user, passwd)
    client.set_timeout(settings.OGC_SERVER['default']['GEOFENCE_TIMEOUT'])
    return client


def get_first_available_priority():
    """Get the highest Rules priority"""
    try:
        client = create_geofence_client()
        rules_count = client.get_rules_count()
        rules_objs = client.get_rules(page=rules_count - 1, entries=1)
        if len(rules_objs['rules']) > 0:
            highest_priority = rules_objs['rules'][0]['priority']
        else:
            highest_priority = 0
        return int(highest_priority) + 1
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        return -1


def purge_geofence_all():
    """purge all existing GeoFence Cache Rules"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        client = create_geofence_client()

        rules_objs = client.get_rules()
        rules = rules_objs['rules']

        batch = Batch('Purge All')
        for rule in rules:
            batch.add_delete_rule(rule['id'])

        logger.debug(f"Going to remove all {len(rules)} rules in geofence")
        client.run_batch(batch)


def create_geofence_purge_dataset_rules(resource, batch=None):
    """purge layer existing GeoFence Cache Rules"""
    # Scan GeoFence Rules associated to the Dataset
    client = create_geofence_client()

    workspace = get_dataset_workspace(resource.dataset)
    dataset_name = resource.dataset.name if resource.dataset and hasattr(resource.dataset, 'name') \
        else resource.dataset.alternate
    try:
        gs_rules = client.get_rules(
            workspace=workspace, workspace_any=False,
            layer=dataset_name, layer_any=False)

        if not batch:
            batch = Batch(f'Purge {workspace}:{dataset_name}')

        if gs_rules and gs_rules['rules']:
            logger.debug(f"Going to remove {len(gs_rules['rules'])} rules for layer '{dataset_name}'")
            for r in gs_rules['rules']:
                if r['layer'] and r['layer'] == dataset_name:
                    batch.add_delete_rule(r['id'])
                else:
                    logger.warning(f"Bad rule retrieved for dataset '{dataset_name}': {r}")

        return batch

    except Exception as e:
        logger.error(f"Error removing rules for {workspace}:{dataset_name}", exc_info=e)
        tb = traceback.format_exc()
        logger.debug(tb)


def purge_geofence_dataset_rules(resource):
    """purge layer existing GeoFence Cache Rules"""
    try:
        batch = create_geofence_purge_dataset_rules(resource)
        client = create_geofence_client()
        client.run_batch(batch)
    except Exception as e:
        workspace = get_dataset_workspace(resource.dataset)
        dataset_name = resource.dataset.name if resource.dataset and hasattr(resource.dataset, 'name') \
            else resource.dataset.alternate

        logger.error(f"Error removing rules for {workspace}:{dataset_name}", exc_info=e)
        tb = traceback.format_exc()
        logger.debug(tb)


def invalidate_geofence_cache():
    """invalidate GeoFence Cache Rules"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            client = create_geofence_client()
            client.invalidate_cache()
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

        client = create_geofence_client()
        priority = get_first_available_priority()

        client.insert_rule(Rule(Rule.ALLOW, priority=priority, workspace=workspace, layer=dataset_name))
    except Exception as e:
        tb = traceback.format_exc()
        logger.debug(tb)
        raise RuntimeError(f"Could not ADD GeoServer ANONYMOUS Rule for Dataset {dataset_name}: {e}")
    finally:
        if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
            invalidate_geofence_cache()
        else:
            resource.set_dirty_state()


# def sync_geofence_with_guardian(dataset, perms, user=None, group=None, group_perms=None):
def create_geofence_rules(dataset, perms, user=None, group=None, batch: Batch = None):
    """
    Collect GeoFence rules related to passed perms into a Batch.
    If the batch does not exist, it is created and returned.
    """
    layer_name = dataset.name if dataset and hasattr(dataset, 'name') else dataset.alternate
    workspace_name = get_dataset_workspace(dataset)
    # Create new rule-set
    gf_services = _get_gf_services(dataset, perms)

    gf_requests = {}
    if 'change_dataset_data' not in perms:
        gf_requests["WFS"] = {
            "TRANSACTION": False,
            "LOCKFEATURE": False,
            "GETFEATUREWITHLOCK": False
        }

    username = (user if isinstance(user, str) else user.username) if user else None
    groupname = (group if isinstance(group, str) else group.name) if group else None

    users_geolimits, groups_geolimits, anonymous_geolimits = get_geolimits(dataset, username, groupname)
    # _disable_cache = has_geolimits(dataset, user, group)
    #
    # if _disable_cache:
    #     gf_services_limits_first = {"*": gf_services.pop('*')}
    #     gf_services_limits_first.update(gf_services)
    #     gf_services = gf_services_limits_first

    if not batch:
        batch = AutoPriorityBatch(get_first_available_priority(), f'Sync {workspace_name}:{layer_name}')

    # Set global geolimits
    # Anon limits should go at the end, but it's responsability of the caller to create first user/group rules
    for limits, scope, u, g in (
            (users_geolimits, 'USER', username, None),
            (anonymous_geolimits, 'ANON', None, None),
            (groups_geolimits, 'GROUP', None, groupname),
    ):
        if limits and limits.exists():
            logger.debug(f"Adding GeoFence {scope} GeoLimit rule: U:{u} G:{g} L:{dataset} ")
            wkt = limits.last().wkt
            batch.add_insert_rule(Rule(Rule.LIMIT,
                                       workspace=workspace_name, layer=layer_name,
                                       user=u, group=g,
                                       geo_limit=wkt, catalog_mode=Rule.CM_MIXED))

    # Set services rules
    for service, allowed in gf_services.items():
        if dataset and layer_name and allowed:
            if username:
                logger.debug(f"Adding GeoFence USER rules: U:{username} S:{service} L:{dataset} ")
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        batch.add_insert_rule(Rule(enabled, user=username,
                                                   workspace=workspace_name, layer=layer_name,
                                                   service=service, request=request))
                batch.add_insert_rule(Rule(Rule.ALLOW, user=username,
                                           workspace=workspace_name, layer=layer_name,
                                           service=service))
            elif not groupname:
                logger.debug(f"Adding GeoFence ANON rules: S:{service} L:{dataset} ")

                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        batch.add_insert_rule(Rule(enabled,
                                                   workspace=workspace_name, layer=layer_name,
                                                   service=service, request=request))

                batch.add_insert_rule(Rule(Rule.ALLOW,
                                           workspace=workspace_name, layer=layer_name,
                                           service=service))
            if groupname:
                logger.debug(f"Adding GeoFence GROUP rules: G:{groupname} S:{service} L:{dataset} ")

                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        batch.add_insert_rule(Rule(enabled, group=groupname,
                                                   workspace=workspace_name, layer=layer_name,
                                                   service=service, request=request))
                batch.add_insert_rule(Rule(Rule.ALLOW, group=groupname,
                                      workspace=workspace_name, layer=layer_name,
                                      service=service))

    return batch


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
    if dirty_resources and dirty_resources.exists():
        logger.debug(" --------------------------- synching with guardian!")

        batch = AutoPriorityBatch(get_first_available_priority(), f"Sync resources {resource if resource else ''}")

        for r in dirty_resources:
            if r.polymorphic_ctype.name == 'dataset':
                layer = None
                try:
                    create_geofence_purge_dataset_rules(r, batch)

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
                            # sync_geofence_with_guardian(layer, perms, user=geofence_user)
                            create_geofence_rules(layer, perms, user=geofence_user, batch=batch)
                    # All the other groups
                    if 'groups' in perm_spec:
                        for group, perms in perm_spec['groups'].items():
                            group = Group.objects.get(name=group)
                            # Set the GeoFence Group Rules
                            # sync_geofence_with_guardian(layer, perms, group=group)
                            create_geofence_rules(layer, perms, group=group, batch=batch)
                    r.clear_dirty_state()
                except Exception as e:
                    logger.exception(e)
                    logger.warning(f"!WARNING! - Failure Synching-up Security Rules for Resource [{r}]")

        try:
            client = create_geofence_client()
            logger.info(f"Going to synch permissions in GeoFence for resource {resource}")
            client.run_batch(batch)
            client.invalidate_cache()
        except Exception as e:
            logger.error(f"ERROR - Could not synchronize GeoFence rules for Resource [{resource}] - Retrying async",
                         exc_info=e)
            resource.set_dirty_state()


def get_geolimits(layer, username, groupname):
    users_geolimits = None
    groups_geolimits = None
    anonymous_geolimits = None

    if username:
        users_geolimits = layer.users_geolimits.filter(user=get_user_model().objects.get(username=username))

    if groupname:
        if GroupProfile.objects.filter(group__name=groupname).exists():
            groups_geolimits = layer.groups_geolimits.filter(group=GroupProfile.objects.get(group__name=groupname))

    if not username and not groupname:
        anonymous_geolimits = layer.users_geolimits.filter(user=get_anonymous_user())

    return users_geolimits, groups_geolimits, anonymous_geolimits


def has_geolimits(layer, user, group):
    if user:
        _user = user if isinstance(user, str) else user.username
        users_geolimits = layer.users_geolimits.filter(user=get_user_model().objects.get(username=_user))
        return users_geolimits.exists()

    if group:
        _group = group if isinstance(group, str) else group.name
        if GroupProfile.objects.filter(group__name=_group).count() == 1:
            groups_geolimits = layer.groups_geolimits.filter(group=GroupProfile.objects.get(group__name=_group))
            return groups_geolimits.exists()

    if not user and not group:
        anonymous_geolimits = layer.users_geolimits.filter(user=get_anonymous_user())
        return anonymous_geolimits.exists()


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


def _get_gwc_filters_and_formats(disable_cache: bool) -> typing.Tuple[list, list]:
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
    if disable_cache:
        filters = None
        formats = None
    return filters, formats
