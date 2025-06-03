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
import time
import json
import datetime
import requests
import traceback

from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from geonode.resource.models import ExecutionRequest
from importer.handlers.base import BaseHandler


class Command(BaseCommand):
    help = (
        "Brings a data file or a directory full of data files into a"
        " GeoNode site. Layers are added to the Django database, the"
        " GeoServer configuration, and the pycsw metadata index."
    )

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="*", help="Path to data file or directory")
        parser.add_argument("-hh", "--host", help="Geonode host URL")
        parser.add_argument("-u", "--username", help="Geonode username")
        parser.add_argument("-p", "--password", help="Geonode password")
        parser.add_argument(
            "-oe", "--overwrite-existing-layers", type=bool, default=False,
            help="Overwrite existing layers"
        )
        parser.add_argument(
            "-se", "--skip-existing-layers", type=bool, default=False,
            help="Skip existing layers (NOT CURRENTLY SUPPORTED IN UPLOAD API)"
        )
        parser.add_argument(
            "-t", "--tentatives", type=int, default=5,
            help="Number of retries for import status check"
        )

    def handle(self, *args, **options):
        if not options["path"]:
            self.print_help('manage.py', 'importlayers')
            return

        host = options.get("host") or getattr(
            settings, "SITEURL", "http://localhost:8000"
        )
        username = options.get("username") or os.getenv("ADMIN_USERNAME", "admin")
        password = options.get("password") or os.getenv("ADMIN_PASSWORD", "admin")
        overwrite_existing_layers = options.get("overwrite_existing_layers", False)
        skip_existing_layers = options.get("skip_existing_layers", False)
        tentatives = options.get("tentatives", 5)

        if skip_existing_layers:
            print(
                "WARNING: The skip_existing_layers flag is not currently "
                "supported in the upload API."
            )
            if overwrite_existing_layers:
                raise ValueError(
                    (
                        "Both overwrite_existing_layers and skip_existing_layers "
                        "cannot be true."
                    )
                )

        start = datetime.datetime.now(timezone.get_current_timezone())

        for path in options["path"]:
            success, errors = GeoNodeUploader(
                host=host, username=username, password=password,
                path=path,
                overwrite_existing_layers=overwrite_existing_layers,
                skip_existing_layers=skip_existing_layers,
                tentatives=tentatives
            ).execute()

            finish = datetime.datetime.now(timezone.get_current_timezone())
            duration = (finish - start).total_seconds()

            if os.path.isdir(path):
                num_files = len(os.listdir(path))
                print(f"{duration / max(num_files, 1)} seconds per layer")
            else:
                print(f"{duration} seconds for the layer")

            print("Importlayers results:")
            print(json.dumps({"success": success, "errors": errors}, indent=4))


class GeoNodeUploader:

    def __init__(
        self, host, path, username, password,
        overwrite_existing_layers, skip_existing_layers, tentatives=5
    ):
        self.host = host
        self.path = path
        self.username = username
        self.password = password
        self.overwrite_existing_layers = overwrite_existing_layers
        self.skip_existing_layers = skip_existing_layers
        self.tentatives = tentatives
        self.handlers = BaseHandler.get_registry()

    def execute(self):
        success, errors = [], []

        if os.path.isfile(self.path):
            # If path is a single file, process it directly
            self.process_file(self.path, success, errors)
        elif os.path.isdir(self.path):
            # If path is a directory, walk through its files
            for root, _, files in os.walk(self.path):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.process_file(file_path, success, errors)
        else:
            print(f"Invalid path: {self.path}")
            errors.append(f"Invalid path: {self.path}")

        return success, errors

    def process_file(self, file_path, success, errors):
        """
        Processes a single file for upload.

        Args:
            file_path (str): The full path to the file being processed.
            success (list): A list to store successfully processed files.
            errors (list): A list to store error messages encountered during processing.
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            errors.append(f"File not found: {file_path}")
            return

        handler = self.get_handler(file_path)
        if not handler and not self.is_archive_file(file_path):
            # Ignore unsupported files
            return

        print(f"Processing: {file_path}")

        if handler:
            required, optional = self.get_related_files(
                handler, file_path, os.path.dirname(file_path)
            )
        else:
            required, optional = ([], [])

        missing = [f for f in required if not os.path.exists(f)]
        if missing:
            missing_err_msg = (
                f"{os.path.basename(file_path)}: Missing required files: {missing}"
            )
            print(missing_err_msg)
            errors.append(missing_err_msg)
            return

        params, files_to_upload = self.prepare_upload_params(
            os.path.basename(file_path), file_path, required, optional
        )
        if self.upload_to_geonode(
            params, files_to_upload, os.path.basename(file_path), errors
        ):
            success.append(os.path.basename(file_path))

    def get_handler(self, file_path):
        """
        Finds the first handler that can process the given file.

        Args:
            file_path (str): The full path to the file being checked.

        Returns:
            BaseHandler or None: The handler capable of processing the file,
            or None if no handler is found.
        """
        if self.is_archive_file(file_path):
            return None

        _data = {"base_file": file_path}
        for handler_class in self.handlers:
            if handler_class.can_handle(_data):
                return handler_class()
        return None

    def is_archive_file(self, file_path):
        """
        Checks if the given file is an archive file (e.g., .zip or .kmz) that does not
        require a handler.

        Archive files are unpacked by the StorageManager after being sent
        to the upload API.

        Args:
            file_path (str): The full path to the file being checked.

        Returns:
            bool: True if the file is an archive, False otherwise.
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in [".zip", ".kmz"]

    def get_related_files(self, handler, file_path, root):
        """
        Determines the required and optional related files for a given dataset file.

        Args:
            handler (BaseHandler): The handler responsible for processing the file.
            file_path (str): The full path to the main file.
            root (str): The root directory containing the file.

        Returns:
            tuple: A list of required file paths and a list of optional file paths.
        """
        config = handler.supported_file_extension_config
        base, _ = os.path.splitext(os.path.basename(file_path))
        required = [
            os.path.join(root, base + f".{ext}")
            for ext in config.get("requires", [])
        ]
        optional = [
            os.path.join(root, base + f".{ext}")
            for ext in config.get("optional", [])
        ]
        return required, optional

    def prepare_upload_params(self, file, file_path, required, optional):
        """
        Prepares the parameters and files required for uploading a dataset to GeoNode.

        Args:
            file (str): The name of the main file being uploaded.
            file_path (str): The full path to the main file.
            required (list): A list of required related file paths.
            optional (list): A list of optional related file paths.

        Returns:
            tuple: A dictionary of parameters (`params`) and a dictionary of files
            to upload (`files_to_upload`).
        """
        params = {
            "dataset_title": file,
            "non_interactive": "true",
            "overwrite_existing_layer": str(self.overwrite_existing_layers).lower(),
            "skip_existing_layers": str(self.skip_existing_layers).lower(),
        }
        files_to_upload = {}

        params["base_file"] = os.path.basename(file_path)
        files_to_upload["base_file"] = open(file_path, "rb")

        if self.is_archive_file(file_path):
            file_ext = os.path.splitext(file_path)[1].lower()
            key = file_ext[1:] + "_file"
            params[key] = os.path.basename(file_path)
            files_to_upload[key] = open(file_path, "rb")

        for f in required + optional:
            if os.path.exists(f):
                key = os.path.splitext(f)[1][1:] + "_file"
                params[key] = os.path.basename(f)
                files_to_upload[key] = open(f, "rb")

        return params, files_to_upload

    def upload_to_geonode(self, params, files_to_upload, file, errors):
        """
        Uploads a dataset to GeoNode using the upload API.

        Args:
            params (dict): A dictionary of parameters required for the upload.
            files_to_upload (dict): A dictionary of file objects to be uploaded.
            file (str): The name of the main file being uploaded.
            errors (list): A list to store error messages encountered during the upload.

        Returns:
            bool: True if the upload is successful, False otherwise.
        """
        client = requests.session()
        print(f"{file}: Submitting to upload API ...")
        response = client.post(
            urljoin(self.host, "/api/v2/uploads/upload/"),
            auth=HTTPBasicAuth(self.username, self.password),
            data=params,
            files=files_to_upload,
        )

        print(f"{file}: Received status code: {response.status_code}")

        for value in files_to_upload.values():
            value.close()

        if response.status_code in [500, 400, 401, 403]:
            upload_error_msg = (
                f"{file}: Error uploading: {response.status_code} - {response.content}"
            )
            print(upload_error_msg)
            errors.append(upload_error_msg)
            return False

        try:
            data = response.json()
            exec_id = data.get("execution_id")
            if not exec_id:
                missing_id_msg = f"{file}: Missing execution_id in response"
                print(missing_id_msg)
                errors.append(missing_id_msg)
                return False

            _exec = ExecutionRequest.objects.get(exec_id=exec_id)
            retries = 0

            while (
                _exec.status.lower() in ["ready", "running"]
                and retries < self.tentatives
            ):
                print(f"{file}: Waiting for upload process to finish ...")
                time.sleep(10)
                _exec.refresh_from_db()
                retries += 1

            if _exec.status.lower() == "running" and retries >= self.tentatives:
                timeout_msg = f"{file}: Timeout waiting for upload process to finish"
                print(timeout_msg)
                errors.append(timeout_msg)
                return False

            if _exec.status.lower() != "finished":
                error_msg = f"{file}: {_exec.log}"
                print(error_msg)
                errors.append(error_msg)
                return False

            print(f"{file}: Upload completed successfully")
            return True
        except json.JSONDecodeError:
            traceback.print_exc()
            return False
