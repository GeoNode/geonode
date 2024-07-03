import os
import logging
from urllib.request import urljoin

from io import IOBase
from django.urls import reverse
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import authenticate

logger = logging.getLogger(__name__)


class ImporterBaseTestSupport(TestCase):
    databases = ("default", "datastore")
    multi_db = True

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        """
        Why manually load the fixture after the setupClass?
        Django in the setUpClass method, load the fixture in all the databases
        that are defined in the databases attribute. The problem is that the
        datastore database will contain only the dyanmic models infrastructure
        and not the whole geonode structure. So that, having the fixture as a
        attribute will raise and error
        """
        fixture = [
            "initial_data.json",
            "group_test_data.json",
            "default_oauth_apps.json",
        ]

        call_command("loaddata", *fixture, **{"verbosity": 0, "database": "default"})


class TransactionImporterBaseTestSupport(TransactionTestCase):
    databases = ("default", "datastore")
    multi_db = True

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        """
        Why manually load the fixture after the setupClass?
        Django in the setUpClass method, load the fixture in all the databases
        that are defined in the databases attribute. The problem is that the
        datastore database will contain only the dyanmic models infrastructure
        and not the whole geonode structure. So that, having the fixture as a
        attribute will raise and error
        """
        fixture = [
            "initial_data.json",
            "group_test_data.json",
            "default_oauth_apps.json",
        ]

        call_command("loaddata", *fixture, **{"verbosity": 0, "database": "default"})


def rest_upload_by_path(_file, client, username="admin", password="admin", non_interactive=False):
    """function that uploads a file, or a collection of files, to
    the GeoNode"""
    assert authenticate(username=username, password=password)
    client.login(username=username, password=password)
    spatial_files = ("dbf_file", "shx_file", "prj_file")
    base, ext = os.path.splitext(_file)
    params = {
        # make public since wms client doesn't do authentication
        "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
        "time": "false",
        "charset": "UTF-8",
    }

    # deal with shapefiles
    if ext.lower() == ".shp":
        for spatial_file in spatial_files:
            ext, _ = spatial_file.split("_")
            file_path = f"{base}.{ext}"
            # sometimes a shapefile is missing an extra file,
            # allow for that
            if os.path.exists(file_path):
                params[spatial_file] = open(file_path, "rb")

    with open(_file, "rb") as base_file:
        params["base_file"] = base_file
        for name, value in params.items():
            if isinstance(value, IOBase):
                params[name] = value
        url = urljoin(f"{reverse('importer_upload')}/", "upload/")
        if non_interactive:
            params["non_interactive"] = "true"
        logger.error(f" ---- UPLOAD URL: {url}")
        response = client.post(url, data=params)

    # Closes the files
    for spatial_file in spatial_files:
        if isinstance(params.get(spatial_file), IOBase):
            params[spatial_file].close()

    try:
        logger.error(f" -- response: {response.status_code} / {response.json()}")
        return response, response.json()
    except (ValueError, TypeError):
        logger.exception(ValueError(f"probably not json, status {response.status_code} / {response.content}"))
        return response, response.content
