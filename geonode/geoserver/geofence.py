#########################################################################
#
# Copyright (C) 2023 OSGeo
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
import urllib
import requests

from django.conf import settings
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

ogc_server_settings = settings.OGC_SERVER['default']


class GeofenceException(Exception):
    pass


class Rule:
    """_summary_
    JSON representation of a GeoFence Rule

    e.g.:
      {"Rule":
        {
          "priority": 0,
          "userName": "admin",
          "service": "WMS",
          "workspace": "geonode",
          "layer": "san_andres_y_providencia_administrative",
          "access": "ALLOW"
        }
      }

    Returns:
        _type_: Rule
    """

    ALLOW = "ALLOW"
    DENY = "DENY"
    LIMIT = "LIMIT"
    CM_MIXED = "MIXED"

    def __init__(self, priority, workspace, layer, access: (str, bool),
                 user=None, group=None,
                 service=None, request=None, subfield=None,
                 geo_limit=None, catalog_mode=None) -> None:
        self.fields = {}

        # access may be either a boolean or ALLOW/DENY/LIMIT
        if access is True:
            access = Rule.ALLOW
        elif access is False:
            access = Rule.DENY

        for field, value in (
            ('priority', priority),

            ('userName', user),
            ('roleName', group),

            ('service', service),
            ('request', request),
            ('subfield', subfield),

            ('workspace', workspace),
            ('layer', layer),

            ('access', access),
        ):
            if value is not None and value != '*':
                self.fields[field] = value

        limits = {}
        for field, value in (
            ('allowedArea', geo_limit),
            ('catalogMode', catalog_mode),
        ):
            if value is not None:
                limits[field] = value

        if limits:
            self.fields['limits'] = limits

    def get_object(self):
        logger.debug(f"Creating Rule object: {self.fields}")
        return {'Rule': self.fields}


class Batch:
    """_summary_
    Returns a list of Operations that GeoFence can execute in a batch

    e.g.:
    {
      "Batch": {
         "operations": [
            {
                "@service": "rules",
                "@type": "insert",
                "Rule": {
                    "priority": 0,
                    "userName": "admin",
                    "service": "WMS",
                    "workspace": "geonode",
                    "layer": "san_andres_y_providencia_administrative",
                    "access": "ALLOW"
                }
            },
            {
                "@service": "rules",
                "@type": "insert",
                "Rule": {
                    "priority": 1,
                    "userName": "admin",
                    "service": "GWC",
                    "workspace": "geonode",
                    "layer": "san_andres_y_providencia_administrative",
                    "access": "ALLOW"
                }
            },
            {
                "@service": "rules",
                "@type": "insert",
                "Rule": {
                    "priority": 2,
                    "userName": "admin",
                    "service": "WFS",
                    "workspace": "geonode",
                    "layer": "san_andres_y_providencia_administrative",
                    "access": "ALLOW"
                }
            },
            {
                "@service": "rules",
                "@type": "insert",
                "Rule": {
                    "priority": 3,
                    "userName": "admin",
                    "service": "WPS",
                    "workspace": "geonode",
                    "layer": "san_andres_y_providencia_administrative",
                    "access": "ALLOW"
                }
            },
            {
                "@service": "rules",
                "@type": "insert",
                "Rule": {
                    "priority": 4,
                    "userName": "admin",
                    "workspace": "geonode",
                    "layer": "san_andres_y_providencia_administrative",
                    "access": "ALLOW"
                }
            }
        ]
      }
    }

    Returns:
        _type_: Batch
    """

    def __init__(self, log_name=None) -> None:
        self.operations = []
        self.log_name = f'"{log_name}"' if log_name else ''

    def __str__(self) -> str:
        return super().__str__()

    def add_delete_rule(self, rule_id: int):
        self.operations.append({
            '@service': 'rules',
            '@type': 'delete',
            '@id': rule_id
        })

    def add_insert_rule(self, rule: Rule):
        operation = {
            '@service': 'rules',
            '@type': 'insert',
        }
        operation.update(rule.get_object())
        self.operations.append(operation)

    def get_batch_length(self):
        return len(self.operations)

    def get_object(self):
        logger.debug(f"Creating Batch object {self.log_name} with {len(self.operations)} operations")
        return {
            'Batch': {
                'operations': self.operations
            }
        }


class GeofenceClient:
    """_summary_
    Instance of a simple GeoFence REST client allowing to interact with the GeoServer APIs.
    Exposes few utility methods to insert or purge the rules and run batches of operations.

    Returns:
        _type_: Rule
    """

    def __init__(self, baseurl: str, username: str, pw: str) -> None:
        self.baseurl = baseurl
        self.username = username
        self.pw = pw

    def invalidate_cache(self):
        r = requests.put(
            f'{self.baseurl.rstrip("/")}/geofence/ruleCache/invalidate',
            auth=HTTPBasicAuth(self.username, self.pw))

        if r.status_code != 200:
            logger.debug("Could not invalidate cache")
            raise GeofenceException("Could not invalidate cache")

    def get_rules(self, page=None, entries=None,
                  workspace=None, workspace_any=None,
                  layer=None, layer_any=None):
        if (page is None and entries is not None) or (page is not None and entries is None):
            raise GeofenceException(f"Bad page/entries combination {page}/{entries}")

        try:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules.json?page={page}&entries={entries}
            """
            params = {}

            if entries:
                params.update({'page': page, 'entries': entries})

            for param, value in (
                ('workspace', workspace),
                ('workspaceAny', workspace_any),
                ('layer', layer),
                ('layerAny', layer_any),
            ):
                if value is not None:
                    params[param] = value

            url = f'{self.baseurl.rstrip("/")}/geofence/rules.json?{urllib.parse.urlencode(params)}'

            r = requests.get(
                url,
                headers={'Content-type': 'application/json'},
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=ogc_server_settings.get('TIMEOUT', 10),
                verify=False)

            if r.status_code != 200:
                logger.debug(f"Could not retrieve GeoFence Rules from {url} -- code:{r.status_code} - {r.text}")
                raise GeofenceException(f"Could not retrieve GeoFence Rules: [{r.status_code}]")

            return r.json()
        except Exception as e:
            logger.debug("Error while retrieving GeoFence rules", exc_info=e)
            raise GeofenceException(f"Error while retrieving GeoFence rules: {e}")

    def get_rules_count(self):
        """Get the number of available GeoFence Rules"""
        try:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules/count.json
            """
            r = requests.get(
                f'{self.baseurl.rstrip("/")}/geofence/rules/count.json',
                headers={'Content-type': 'application/json'},
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=ogc_server_settings.get('TIMEOUT', 10),
                verify=False)

            if r.status_code != 200:
                logger.debug(f"Could not retrieve GeoFence Rules count: [{r.status_code}] - {r.text}")
                raise GeofenceException(f"Could not retrieve GeoFence Rules count: [{r.status_code}]")

            response = r.json()
            return response['count']

        except Exception as e:
            logger.debug("Error while retrieving GeoFence rules count", exc_info=e)
            raise GeofenceException(f"Error while retrieving GeoFence rules count: {e}")

    def insert_rule(self, rule: Rule):
        try:
            """
            curl -X POST -u admin:geoserver -H "Content-Type: text/xml" -d \
            "<Rule><workspace>geonode</workspace><layer>{layer}</layer><access>ALLOW</access></Rule>" \
            http://<host>:<port>/geoserver/rest/geofence/rules
            """
            r = requests.post(
                f'{self.baseurl.rstrip("/")}/geofence/rules',
                # headers={'Content-type': 'application/json'},
                json=rule.get_object(),
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=ogc_server_settings.get('TIMEOUT', 60),
                verify=False)

            if r.status_code not in (200, 201):
                logger.debug(f"Could not insert rule: [{r.status_code}] - {r.content}")
                raise GeofenceException(f"Could not insert rule: [{r.status_code}]")

        except Exception as e:
            logger.debug("Error while inserting rule", exc_info=e)
            raise GeofenceException(f"Error while inserting rule: {e}")

    def run_batch(self, batch: Batch):
        if batch.get_batch_length() == 0:
            logger.debug(f'Skipping batch execution {batch.log_name}')
            return

        try:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules/count.json
            """
            r = requests.post(
                f'{self.baseurl.rstrip("/")}/geofence/batch/exec',
                json=batch.get_object(),
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=ogc_server_settings.get('TIMEOUT', 60),
                verify=False)

            if r.status_code != 200:
                logger.debug(f"Error while running batch {batch.log_name}: [{r.status_code}] - {r.content}")
                raise GeofenceException(f"Error while running batch {batch.log_name}: [{r.status_code}]")

            return

        except Exception as e:
            logger.debug(f"Error while requesting batch execution {batch.log_name}", exc_info=e)
            raise GeofenceException(f"Error while requesting batch execution {batch.log_name}: {e}")

    def purge_all_rules(self):
        """purge all existing GeoFence Cache Rules"""
        rules_objs = self.get_rules()
        rules = rules_objs['rules']

        batch = Batch('Purge All')
        for rule in rules:
            batch.add_delete_rule(rule['id'])

        logger.debug(f"Going to remove all {len(rules)} rules in geofence")
        self.run_batch(batch)

    def purge_layer_rules(self, layer_name: str, workspace: str = None):
        """purge existing GeoFence Cache Rules related to a specific Layer"""
        gs_rules = self.get_rules(
            workspace=workspace, workspace_any=False,
            layer=layer_name, layer_any=False)

        batch = Batch(f'Purge {workspace}:{layer_name}')

        if gs_rules and gs_rules['rules']:
            logger.debug(f"Going to remove {len(gs_rules['rules'])} rules for layer '{layer_name}'")
            for r in gs_rules['rules']:
                if r['layer'] and r['layer'] == layer_name:
                    batch.add_delete_rule(r['id'])
                else:
                    logger.debug(f"Bad rule retrieved for dataset '{layer_name}': {r}")
        self.run_batch(batch)
