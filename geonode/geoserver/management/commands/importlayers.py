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
import os
import json
import argparse
import datetime
import requests
import traceback

from urllib.parse import urljoin
from io import BufferedReader, IOBase
from requests.auth import HTTPBasicAuth

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand

parser = argparse.ArgumentParser()


class Command(BaseCommand):
    help = (
        "Brings a data file or a directory full of data files into a"
        " GeoNode site.  Layers are added to the Django database, the"
        " GeoServer configuration, and the pycsw metadata index."
    )

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("path", nargs="*", help="path [path...]")

        parser.add_argument("-hh", "--host", dest="host", help="Geonode host url")

        parser.add_argument("-u", "--username", dest="username", help="Geonode username")

        parser.add_argument("-p", "--password", dest="password", help="Geonode password")

    def handle(self, *args, **options):
        if not len(options["path"]) > 0:
            self.print_help('manage.py', 'importlayers')
            return

        host = options.get("host") or getattr(settings, "SITEURL", "http://localhost:8000")
        username = options.get("username") or os.getenv("ADMIN_USERNAME", "admin")
        password = options.get("password") or os.getenv("ADMIN_PASSWORD", "admin")

        start = datetime.datetime.now(timezone.get_current_timezone())
        for path in options["path"]:
            success, errors = GeoNodeUploader(
                host=host, username=username, password=password, folder_path=path
            ).execute()

            finish = datetime.datetime.now(timezone.get_current_timezone())
            td = finish - start
            duration = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600

            print(f"{(duration * 1.0 / len(os.listdir(options['path'][0])))} seconds per layer")

            output = {"success": success, "errors": errors}
            print(f"Output data: {output}")


class GeoNodeUploader:

    def __init__(
        self,
        host: str,
        folder_path: str,
        username: str,
        password: str,
        call_delay: int = 10,
        **kwargs,
    ):
        self.host = host
        self.folder_path = folder_path
        self.username = username
        self.password = password
        self.call_delay = call_delay

    def execute(self):
        success = []
        errors = []
        for root, subdirs, files in os.walk(self.folder_path):
            for file in files:
                _file = os.path.join(root, file)
                print(f"Scanning: {_file}")
                if not os.path.exists(_file):
                    print(f"The selected file path does not exist: {_file}")
                    continue
                spatial_files = ("dbf_file", "shx_file", "prj_file", "xml_file", "sld_file")
                base, ext = os.path.splitext(_file)
                params = {
                    # make public since wms client doesn't do authentication
                    "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',  # to be decided
                    "time": "false",
                    "dataset_title": file,
                    "charset": "UTF-8",
                }

                if ext.lower() == ".shp":
                    for spatial_file in spatial_files:
                        ext, _ = spatial_file.split("_")
                        file_path = f"{base}.{ext}"
                        # sometimes a shapefile is missing an extra file,
                        # allow for that
                        if os.path.exists(file_path):
                            params[spatial_file] = open(file_path, "rb")
                elif ext.lower() in (".tif", ".zip"):
                    file_path = base + ext
                    params["tif_file"] = open(file_path, "rb")
                    if os.path.exists(f'{base}.xml'):
                        params["xml_file"] = open(f'{base}.xml', "rb")

                else:
                    continue

                files = {}

                client = requests.session()

                with open(_file, "rb") as base_file:
                    params["base_file"] = base_file
                    for name, value in params.items():
                        if isinstance(value, BufferedReader):
                            files[name] = (os.path.basename(value.name), value)
                            params[name] = os.path.basename(value.name)

                    params["non_interactive"] = 'true'
                    response = client.post(
                        urljoin(self.host, "/api/v2/uploads/upload/"),
                        auth=HTTPBasicAuth(self.username, self.password),
                        data=params,
                        files=files,
                    )
                    print(f"{file}: {response.status_code}")

                if isinstance(params.get("tif_file"), IOBase):
                    params["tif_file"].close()

                try:
                    if response.status_code in [500, 400, 403]:
                        raise Exception(response.content)
                    data = response.json()
                    if not data.get('status', None):
                        raise Exception(data)
                    if data.get('status', '') == 'finished':
                        if data['success']:
                            success.append(file)
                        else:
                            errors.append(file)
                    else:
                        errors.append(file)
                except json.JSONDecodeError:
                    traceback.print_exc()
                    errors.append(file)
        return success, errors

    @staticmethod
    def _get_upload_id(upload_response, import_id):
        for item in upload_response.json()["uploads"]:
            if item.get("import_id", None) == import_id:
                return item.get("id", None)
