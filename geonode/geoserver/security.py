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
import requests
import traceback
from packaging import version
import re
import typing
import xml.etree.ElementTree as ET

from lxml import etree
from defusedxml import lxml as dlxml
from requests.auth import HTTPBasicAuth
from guardian.shortcuts import get_anonymous_user

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from geonode.geoserver.geofence import Batch, Rule, AutoPriorityBatch
from geonode.geoserver.helpers import geofence, gf_utils, gs_catalog
from geonode.groups.models import GroupProfile
from geonode.utils import get_dataset_workspace


logger = logging.getLogger(__name__)


def delete_all_geofence_rules():
    """purge all existing GeoFence Rules"""
    if settings.OGC_SERVER["default"]["GEOFENCE_SECURITY_ENABLED"] or getattr(
        settings, "GEOFENCE_SECURITY_ENABLED", False
    ):
        gf_utils.delete_all_rules()


def delete_geofence_rules_for_layer(instance):
    """Delete all rules for a given layer
    This function wraps the gf_util method, since it doesn't know about Dataset model
    """
    if settings.OGC_SERVER["default"]["GEOFENCE_SECURITY_ENABLED"] or getattr(
        settings, "GEOFENCE_SECURITY_ENABLED", False
    ):
        resource = instance.get_self_resource()
        workspace_name = get_dataset_workspace(resource.dataset)
        layer_name = (
            resource.dataset.name
            if resource.dataset and hasattr(resource.dataset, "name")
            else resource.dataset.alternate
        )
        logger.debug(f"Removing rules for layer {workspace_name}:{layer_name}")
        gf_utils.delete_layer_rules(workspace_name, layer_name)


def invalidate_geofence_cache():
    """invalidate GeoFence Cache Rules"""
    if settings.OGC_SERVER["default"]["GEOFENCE_SECURITY_ENABLED"]:
        try:
            geofence.invalidate_cache()
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


def toggle_dataset_cache(dataset_name, enable=True, filters=None, formats=None):
    """Disable/enable a GeoServer Tiled Dataset Configuration"""
    if settings.OGC_SERVER["default"]["GEOFENCE_SECURITY_ENABLED"]:
        try:
            url = settings.OGC_SERVER["default"]["LOCATION"]
            user = settings.OGC_SERVER["default"]["USER"]
            passwd = settings.OGC_SERVER["default"]["PASSWORD"]
            """
            curl -v -u admin:geoserver -XGET \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.get(f"{url}gwc/rest/layers/{dataset_name}.xml", auth=HTTPBasicAuth(user, passwd))

            if r.status_code < 200 or r.status_code > 201:
                logger.debug(f"Could not Retrieve {dataset_name} Cache.")
                return False
            try:
                xml_content = r.content
                tree = dlxml.fromstring(xml_content)

                gwc_id = tree.find("id")
                tree.remove(gwc_id)

                gwc_enabled = tree.find("enabled")
                if gwc_enabled is None:
                    gwc_enabled = etree.Element("enabled")
                    tree.append(gwc_enabled)
                gwc_enabled.text = str(enable).lower()

                gwc_mimeFormats = tree.find("mimeFormats")
                # Returns an element instance or None
                if gwc_mimeFormats is not None and len(gwc_mimeFormats):
                    tree.remove(gwc_mimeFormats)

                if formats is not None:
                    for format in formats:
                        gwc_format = etree.Element("string")
                        gwc_format.text = format
                        gwc_mimeFormats.append(gwc_format)

                    tree.append(gwc_mimeFormats)

                gwc_parameterFilters = tree.find("parameterFilters")
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
                                gwc_parameter_key = etree.Element("key")
                                gwc_parameter_key.text = parameter_key
                                gwc_parameter_value = etree.Element("defaultValue")
                                gwc_parameter_value.text = parameter_value

                                gwc_parameter.append(gwc_parameter_key)
                                gwc_parameter.append(gwc_parameter_value)
                            gwc_parameterFilters.append(gwc_parameter)

                """
                curl -v -u admin:geoserver -XPOST \
                    -H "Content-type: text/xml" -d @poi.xml \
                        "http://localhost:8080/geoserver/gwc/rest/layers/tiger:poi.xml"
                """
                headers = {"Content-type": "text/xml"}
                payload = ET.tostring(tree)
                r = requests.post(
                    f"{url}gwc/rest/layers/{dataset_name}.xml",
                    headers=headers,
                    data=payload,
                    auth=HTTPBasicAuth(user, passwd),
                )
                if r.status_code < 200 or r.status_code > 201:
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
    if settings.OGC_SERVER["default"]["GEOFENCE_SECURITY_ENABLED"]:
        try:
            url = settings.OGC_SERVER["default"]["LOCATION"]
            user = settings.OGC_SERVER["default"]["USER"]
            passwd = settings.OGC_SERVER["default"]["PASSWORD"]
            """
            curl -v -u admin:geoserver -XDELETE \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.delete(f"{url}gwc/rest/layers/{dataset_name}.xml", auth=HTTPBasicAuth(user, passwd))

            if r.status_code < 200 or r.status_code > 201:
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
                url = settings.OGC_SERVER["default"]["LOCATION"]
                user = settings.OGC_SERVER["default"]["USER"]
                passwd = settings.OGC_SERVER["default"]["PASSWORD"]
                """
                curl -v -u admin:geoserver \
                -H "Content-type: text/xml" \
                -d "<truncateLayer><layerName>{dataset_alternate}</layerName></truncateLayer>" \
                http://localhost:8080/geoserver/gwc/rest/masstruncate
                """
                headers = {"Content-type": "text/xml"}
                payload = f"<truncateLayer><layerName>{dataset_alternate}</layerName></truncateLayer>"
                r = requests.post(
                    f"{url.rstrip('/')}/gwc/rest/masstruncate",
                    headers=headers,
                    data=payload,
                    auth=HTTPBasicAuth(user, passwd),
                )
                if r.status_code < 200 or r.status_code > 201:
                    logger.debug(f"Could not Truncate GWC Cache for Dataset '{dataset_alternate}'.")
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)


def allow_layer_to_all(instance):
    """assign access permissions to all users

    This method is only relevant to Dataset instances that have their
    underlying data managed by geoserver, meaning:

    * layers that are not associated with a Service
    * layers that are associated with a Service that is being CASCADED through
      geoserver

    """
    resource = instance.get_self_resource()
    logger.debug(f"Inside allow_layer_to_all for instance {instance}")
    workspace = get_dataset_workspace(resource.dataset)
    dataset_name = (
        resource.dataset.name if resource.dataset and hasattr(resource.dataset, "name") else resource.dataset.alternate
    )
    logger.debug(f"Allowing {workspace}:{dataset_name} access to everybody")
    try:
        priority = gf_utils.get_first_available_priority()
        geofence.insert_rule(Rule(Rule.ALLOW, priority=priority, workspace=workspace, layer=dataset_name))
    except Exception as e:
        tb = traceback.format_exc()
        logger.debug(tb)
        raise RuntimeError(f"Could not ADD GeoServer ANONYMOUS Rule for Dataset {dataset_name}: {e}")
    finally:
        if not getattr(settings, "DELAYED_SECURITY_SIGNALS", False):
            invalidate_geofence_cache()
        else:
            resource.set_dirty_state()


# def sync_geofence_with_guardian(dataset, perms, user=None, group=None, group_perms=None):
def create_geofence_rules(layer, perms, user=None, group=None, batch: Batch = None):
    """
    Collect GeoFence rules related to passed perms into a Batch.
    If the batch does not exist, it is created and returned.
    """
    if user and group:
        raise ValueError("Both user and group given")

    layer_name = layer.name if layer and hasattr(layer, "name") else layer.alternate
    workspace_name = get_dataset_workspace(layer)
    # Create new rule-set
    gf_services = _get_gf_services(layer, perms)

    username = (user if isinstance(user, str) else user.username) if user else None
    groupname = (group if isinstance(group, str) else group.name) if group else None

    users_geolimits, groups_geolimits, anonymous_geolimits = get_geolimits(layer, username, groupname)

    if not batch:
        batch = AutoPriorityBatch(gf_utils.get_first_available_priority(), f"Sync {workspace_name}:{layer_name}")

    # Set global geolimits
    # Anon limits should go at the end, but it's responsibility of the caller to create first user/group rules
    for limits, scope, u, g in (
        (users_geolimits, "USER", username, None),
        (groups_geolimits, "GROUP", None, groupname),
        (anonymous_geolimits, "ANON", None, None),
    ):
        if limits and limits.exists():
            logger.debug(f"Adding GeoFence {scope} GeoLimit rule: U:{u} G:{g} L:{layer} ")
            wkt = limits.last().wkt
            batch.add_insert_rule(
                Rule(
                    Rule.LIMIT,
                    workspace=workspace_name,
                    layer=layer_name,
                    user=u,
                    group=g,
                    geo_limit=wkt,
                    catalog_mode=Rule.CM_MIXED,
                )
            )

    if username:
        msg = "Adding GeoFence USER rules: U:{username} S:{service} L:{layer} "
    elif not groupname:
        msg = "Adding GeoFence ANON rules: S:{service} L:{layer} "
    if groupname:
        msg = "Adding GeoFence GROUP rules: G:{groupname} S:{service} L:{layer} "

    # Set services rules
    for rule_fields in gf_services:
        if layer and layer_name:
            logger.debug(msg.format(username=username, groupname=groupname, layer=layer_name, **rule_fields))
            batch.add_insert_rule(
                Rule(
                    user=username,
                    group=groupname,
                    workspace=workspace_name,
                    layer=layer_name,
                    **rule_fields,  # access, service, request, subfield
                )
            )

    return batch


def sync_resources_with_guardian(resource=None, force=False):
    """
    Sync resources with Guardian and clear their dirty state
    """
    from geonode.layers.models import Dataset

    if resource:
        datasets = Dataset.objects.filter(id=resource.id)
    else:
        if force:
            datasets = Dataset.objects.all()
        else:
            datasets = Dataset.objects.filter(dirty_state=True)
    if datasets and datasets.exists():
        logger.debug(" --------------------------- synching with guardian!")

        rules_committed = False

        for dataset in datasets:
            try:
                batch = AutoPriorityBatch(gf_utils.get_first_available_priority(), f"Sync resources {dataset}")

                gf_utils.collect_delete_layer_rules(get_dataset_workspace(dataset), dataset.name, batch)

                perm_spec = dataset.get_all_level_info()
                # All the other users
                if "users" in perm_spec:
                    for user, perms in perm_spec["users"].items():
                        user = get_user_model().objects.get(username=user)
                        # Set the GeoFence User Rules
                        geofence_user = str(user)
                        if "AnonymousUser" in geofence_user or str(get_anonymous_user()) in geofence_user:
                            geofence_user = None
                        create_geofence_rules(dataset, perms, user=geofence_user, batch=batch)
                # All the other groups
                if "groups" in perm_spec:
                    for group, perms in perm_spec["groups"].items():
                        group = Group.objects.get(name=group)
                        if group and group.name and group.name == "anonymous":
                            group = None
                        # Set the GeoFence Group Rules
                        create_geofence_rules(dataset, perms, group=group, batch=batch)

                logger.info(f"Going to synch permissions in GeoFence for resource {dataset}")
                rules_committed = geofence.run_batch(batch)
                dataset.clear_dirty_state()
            except Exception as e:
                logger.exception(e)
                logger.warning(f"!WARNING! - Failure Synching-up Security Rules for Resource [{dataset}]")

        if rules_committed:
            invalidate_geofence_cache()


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
    edit = "change_dataset_data" in perms
    download = "download_resourcebase" in perms
    view = "view_resourcebase" in perms

    gf_services = []

    # view services
    if view or "change_dataset_style" in perms:
        gf_services.append({"service": "WMS", "access": True})
        gf_services.append({"service": "GWC", "access": True})

    # WPS
    if view or download or edit:
        if not download:
            if geoserver_allows_wps_rules(gs_catalog.get_version()):
                gf_services.append({"service": "WPS", "subfield": "GS:DOWNLOAD", "access": False})
        gf_services.append({"service": "WPS", "access": True})

    if download and not edit and layer.is_vector():
        for request in ("TRANSACTION", "LOCKFEATURE", "GETFEATUREWITHLOCK"):
            gf_services.append({"service": "WFS", "request": request, "access": False})

    if download or edit:
        service = "WFS" if layer.is_vector() else "WCS"
        gf_services.append({"service": service, "access": True})

    # TODO: check if this rule is really needed
    if download and (view or edit):
        gf_services.append({"service": "*", "access": True})

    return gf_services


def geoserver_allows_wps_rules(ver: str) -> bool:
    try:
        s = re.search(r"^[0-9]\.[0-9]*", ver)
        if s:
            ver_clean = s.group()
            return version.parse(ver_clean) >= version.parse("2.23.0")
        else:
            logger.warning(f'Unparsable GeoServer version string "{ver}"')

    except Exception as e:
        logger.warning(f'Error evaluating GeoServer version "{ver}": {e}')

    return False


def _get_gwc_filters_and_formats(disable_cache: bool) -> typing.Tuple[list, list]:
    filters = [{"styleParameterFilter": {"STYLES": ""}}]
    formats = [
        "application/json;type=utfgrid",
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/png8",
        "image/vnd.jpeg-png",
        "image/vnd.jpeg-png8",
    ]
    if disable_cache:
        filters = None
        formats = None
    return filters, formats
