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

import itertools
import logging
import requests
from requests.auth import HTTPBasicAuth
import traceback
import urllib

logger = logging.getLogger(__name__)


class GeofenceException(Exception):
    pass


class Rule:
    """_summary_
    A GeoFence Rule.
    Provides the object to be rendered as JSON.

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

    def __init__(
        self,
        access: (str, bool),
        priority=None,
        workspace=None,
        layer=None,
        user=None,
        group=None,
        service=None,
        request=None,
        subfield=None,
        geo_limit=None,
        catalog_mode=None,
    ) -> None:
        self.fields = {}

        # access may be either a boolean or ALLOW/DENY/LIMIT
        if access is True:
            access = Rule.ALLOW
        elif access is False:
            access = Rule.DENY

        for field, value in (
            ("priority", priority),
            ("userName", user),
            ("roleName", f"ROLE_{group.upper()}" if group is not None and group != "*" else group),
            ("service", service),
            ("request", request),
            ("subfield", subfield),
            ("workspace", workspace),
            ("layer", layer),
            ("access", access),
        ):
            if value is not None and value != "*":
                self.fields[field] = value

        limits = {}
        for field, value in (
            ("allowedArea", geo_limit),
            ("catalogMode", catalog_mode),
        ):
            if value is not None:
                limits[field] = value

        if limits:
            self.fields["limits"] = limits

    def set_priority(self, pri: int):
        self.fields["priority"] = pri

    def get_object(self) -> dict:
        logger.debug(f"Creating Rule object: {self.fields}")
        return {"Rule": self.fields}


class Batch:
    """_summary_
    A GeoFence Batch.
    It's a list of operations that will be executed transactionally inside GeoFence.

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
        self.log_name = f'"{log_name}"' if log_name else ""

    def __str__(self) -> str:
        return super().__str__()

    def add_delete_rule(self, rule_id: int):
        self.operations.append({"@service": "rules", "@type": "delete", "@id": rule_id})

    def add_insert_rule(self, rule: Rule):
        operation = {
            "@service": "rules",
            "@type": "insert",
        }
        operation.update(rule.get_object())
        self.operations.append(operation)

    def length(self) -> int:
        return len(self.operations)

    def get_object(self) -> dict:
        return {"Batch": {"operations": self.operations}}


class AutoPriorityBatch(Batch):
    """_summary_
    A Batch that handles the priority of the inserted rules.
    The first rule will have the declared `start_rule_pri`, next Rules will have the priority incremented.
    """

    def __init__(self, start_rule_pri: int, log_name=None) -> None:
        super().__init__(log_name)
        self.pri = itertools.count(start_rule_pri)

    def add_insert_rule(self, rule: Rule):
        rule.set_priority(self.pri.__next__())
        super().add_insert_rule(rule)


class GeoFenceClient:
    """_summary_
    A GeoFence REST client allowing to interact with the embedded GeoFence API (which is slightly incompatible
       with the original standalone GeoFence API.)
    The class methods map on GeoFence operations.
    Functionalities needing more than one call are implemented within GeoFenceUtils.
    """

    def __init__(self, baseurl: str, username: str, pw: str) -> None:
        if not baseurl.endswith("/"):
            baseurl += "/"

        self.baseurl = baseurl
        self.username = username
        self.pw = pw
        self.timeout = 60

    def set_timeout(self, timeout: int):
        self.timeout = timeout

    def invalidate_cache(self):
        r = requests.put(f"{self.baseurl}ruleCache/invalidate", auth=HTTPBasicAuth(self.username, self.pw))

        if r.status_code != 200:
            logger.debug("Could not invalidate cache")
            raise GeofenceException("Could not invalidate cache")

    def get_rules(
        self,
        page: int = None,
        entries: int = None,
        workspace: str = None,
        workspace_any: bool = None,
        layer: str = None,
        layer_any: bool = None,
    ):
        if (page is None and entries is not None) or (page is not None and entries is None):
            raise GeofenceException(f"Bad page/entries combination {page}/{entries}")

        try:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules.json?page={page}&entries={entries}
            """
            params = {}

            if entries:
                params.update({"page": page, "entries": entries})

            for param, value in (
                ("workspace", workspace),
                ("workspaceAny", workspace_any),
                ("layer", layer),
                ("layerAny", layer_any),
            ):
                if value is not None:
                    params[param] = value

            url = f"{self.baseurl}rules.json?{urllib.parse.urlencode(params)}"

            r = requests.get(
                url,
                headers={"Content-type": "application/json"},
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=self.timeout,
                verify=False,
            )

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
                f"{self.baseurl}rules/count.json",
                headers={"Content-type": "application/json"},
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=self.timeout,
                verify=False,
            )

            if r.status_code != 200:
                logger.debug(f"Could not retrieve GeoFence Rules count: [{r.status_code}] - {r.text}")
                raise GeofenceException(f"Could not retrieve GeoFence Rules count: [{r.status_code}]")

            response = r.json()
            return response["count"]

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
                f"{self.baseurl}rules",
                json=rule.get_object(),
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=self.timeout,
                verify=False,
            )

            if r.status_code not in (200, 201):
                logger.debug(f"Could not insert rule: [{r.status_code}] - {r.text}")
                raise GeofenceException(f"Could not insert rule: [{r.status_code}] - {r.text}")

        except Exception as e:
            logger.debug("Error while inserting rule", exc_info=e)
            raise GeofenceException(f"Error while inserting rule: {e}")

    def run_batch(self, batch: Batch, timeout: int = None) -> bool:
        if batch.length() == 0:
            logger.debug(f"Skipping batch execution {batch.log_name}")
            return False

        logger.debug(f"Running batch {batch.log_name} with {batch.length()} operations")
        try:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules/count.json
            """
            r = requests.post(
                f"{self.baseurl}batch/exec",
                json=batch.get_object(),
                auth=HTTPBasicAuth(self.username, self.pw),
                timeout=timeout or self.timeout,
                verify=False,
            )

            if r.status_code != 200:
                logger.debug(
                    f"Error while running batch {batch.log_name}: [{r.status_code}] - {r.content}"
                    f"\n {batch.get_object()}"
                )
                raise GeofenceException(f"Error while running batch {batch.log_name}: [{r.status_code}]")

            return True

        except Exception as e:
            logger.info(f"Error while requesting batch exec {batch.log_name}")
            logger.debug(f"Error while requesting batch exec {batch.log_name} --> {batch.get_object()}", exc_info=e)
            raise GeofenceException(f"Error while requesting batch execution {batch.log_name}: {e}")


class GeoFenceUtils:
    def __init__(self, client: GeoFenceClient):
        self.geofence = client

    def delete_all_rules(self):
        """purge all existing GeoFence Cache Rules"""
        rules_objs = self.geofence.get_rules()
        rules = rules_objs["rules"]

        batch = Batch("Purge All")
        for rule in rules:
            batch.add_delete_rule(rule["id"])

        logger.debug(f"Going to remove all {len(rules)} rules in geofence")
        self.geofence.run_batch(batch)

    def collect_delete_layer_rules(self, workspace_name: str, layer_name: str, batch: Batch = None) -> Batch:
        """Collect delete operations in a Batch for all rules related to a layer"""

        try:
            # Scan GeoFence Rules associated to the Dataset
            gs_rules = self.geofence.get_rules(
                workspace=workspace_name, workspace_any=False, layer=layer_name, layer_any=False
            )

            if not batch:
                batch = Batch(f"Delete {workspace_name}:{layer_name}")

            cnt = 0
            if gs_rules and gs_rules["rules"]:
                logger.debug(
                    f"Going to collect {len(gs_rules['rules'])} rules for layer '{workspace_name}:{layer_name}'"
                )
                for r in gs_rules["rules"]:
                    if r["layer"] and r["layer"] == layer_name:
                        batch.add_delete_rule(r["id"])
                        cnt += 1
                    else:
                        logger.warning(f"Bad rule retrieved for dataset '{workspace_name or ''}:{layer_name}': {r}")

            logger.debug(f"Adding {cnt} rule deletion operations for '{workspace_name or ''}:{layer_name}")
            return batch

        except Exception as e:
            logger.error(f"Error collecting rules for {workspace_name}:{layer_name}", exc_info=e)
            tb = traceback.format_exc()
            logger.debug(tb)

    def delete_layer_rules(self, workspace_name: str, layer_name: str) -> bool:
        """Delete all Rules related to a specific Layer"""
        try:
            batch = self.collect_delete_layer_rules(workspace_name, layer_name)
            if not batch:
                logger.error(f"Error removing rules for {workspace_name}:{layer_name}")
                return False

            logger.debug(f"Going to remove {batch.length()} rules for layer {workspace_name}:{layer_name}")
            return self.geofence.run_batch(batch)

        except Exception as e:
            logger.error(f"Error removing rules for {workspace_name}:{layer_name}", exc_info=e)
            tb = traceback.format_exc()
            logger.debug(tb)
            return False

    def get_first_available_priority(self):
        """Get the highest Rules priority"""
        try:
            rules_count = self.geofence.get_rules_count()
            rules_objs = self.geofence.get_rules(page=rules_count - 1, entries=1)
            if len(rules_objs["rules"]) > 0:
                highest_priority = rules_objs["rules"][0]["priority"]
            else:
                highest_priority = 0
            return int(highest_priority) + 1
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return -1
