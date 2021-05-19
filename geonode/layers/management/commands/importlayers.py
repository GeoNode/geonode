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

from io import BufferedReader
import os
from django.utils import timezone
from django.core.management.base import BaseCommand
import requests
import datetime
from io import BufferedReader, IOBase
import os
import requests
import argparse

parser=argparse.ArgumentParser()

class GeoNodeUploader():
    def __init__(
        self,
        host: str,
        folder_path: str,
        username: str,
        password: str,
        call_delay: int = 10,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.host = host
        self.folder_path = folder_path
        self.username = username
        self.password = password
        self.call_delay = call_delay

    def execute(self):

        for file in os.listdir(self.folder_path):
            if not os.path.exists(f"{self.folder_path}/{file}"):
                print(f"The selected file path does not exist: {file}")
                continue

            _file = f"{self.folder_path}/{file}"
            spatial_files = ("dbf_file", "shx_file", "prj_file")

            base, ext = os.path.splitext(_file)
            params = {
                # make public since wms client doesn't do authentication
                "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',  # to be decided
                "time": "false",
                "layer_title": file,
                "time": "false",
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
            elif ext.lower() == ".tif":
                file_path = base + ext
                params["tif_file"] = open(file_path, "rb")
            else:
                continue
            print(f"Starting upload for file: {self.folder_path}/{file}")

            print(f"Generating params dict: {params}")

            files = {}

            print("Opening client session")

            client = requests.session()

            print("Opening Files")
            with open(_file, "rb") as base_file:
                params["base_file"] = base_file
                for name, value in params.items():
                    if isinstance(value, BufferedReader):
                        files[name] = (os.path.basename(value.name), value)
                        params[name] = os.path.basename(value.name)

                print(
                    f"Sending PUT request to geonode: {self.host}/api/v2/uploads/upload/"
                )

                headers = {"Authorization": "Bearer token"}

                response = client.put(
                    f"{self.host}/api/v2/uploads/upload/",
                    headers=headers,
                    data=params,
                    files=files,
                )

                print(f"Geonode response with status code {response.status_code}")

            print("Closing spatial files")

            if isinstance(params.get("tif_file"), IOBase):
                params["tif_file"].close()

            print("Getting import_id")
            import_id = int(response.json()["redirect_to"].split("?id=")[1].split("&")[0])
            print(f"ImportID found with ID: {import_id}")

            print(f"Getting upload_list")
            upload_response = client.get(f"{self.host}/api/v2/uploads/")

            print(f"Extraction of upload_id")

            upload_id = self._get_upload_id(upload_response, import_id)

            print(f"UploadID found {upload_id}")

            print(f"Calling upload detail page")
            client.get(f"{self.host}/api/v2/uploads/{upload_id}")

            print(f"Calling final upload page")
            client.get(f"{self.host}/upload/final?id={import_id}")

            print(f"Layer added in GeoNode")

    @staticmethod
    def _get_upload_id(upload_response, import_id):
        for item in upload_response.json()["uploads"]:
            if item.get("import_id", None) == import_id:
                return item.get("id", None)

class Command(BaseCommand):
    help = ("Brings a data file or a directory full of data files into a"
            " GeoNode site.  Layers are added to the Django database, the"
            " GeoServer configuration, and the pycsw metadata index.")

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('path', nargs='*', help='path [path...]')

        parser.add_argument(
            '-hh',
            '--host',
            dest='host',
            help="Geonode host url")

        parser.add_argument(
            '-u',
            '--username',
            dest='username',
            help="Geonode username")

        parser.add_argument(
            '-p',
            '--password',
            dest='password',
            help="Geonode password")

    def handle(self, *args, **options):
        host = options.get('host') or "http://localhost:8000"
        username = options.get('username') or 'admin'
        password = options.get('password') or "admin"

        start = datetime.datetime.now(timezone.get_current_timezone())

        GeoNodeUploader(
            host=host,
            username=username,
            password=password,
            folder_path=options['path'][0]
        ).execute()

        finish = datetime.datetime.now(timezone.get_current_timezone())
        td = finish - start
        duration = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600
        duration_rounded = round(duration, 2)

        print(f"{(duration * 1.0 / len(os.listdir(options['path'])))} seconds per layer")
