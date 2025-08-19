import os
from pathlib import Path
import zipfile


def organize_files_by_ext(input_data):
    file_paths = {}
    from geonode.utils import get_allowed_extensions

    available_choices = get_allowed_extensions()
    not_main_files = ["xml", "sld", "zip", "kmz"]
    base_file_choices = [x for x in available_choices if x not in not_main_files]

    if not isinstance(input_data, list) and os.path.isdir(input_data):
        input_data = Path(input_data).iterdir()
    sorted_files = sorted(Path(data) for data in input_data)

    for _file in sorted_files:
        if not zipfile.is_zipfile(str(_file)):
            if any([_file.name.endswith(_ext) for _ext in base_file_choices]):
                file_paths["base_file"] = Path(str(_file))
            ext = _file.name.split(".")[-1]
            if f"{ext}_file" in file_paths:
                existing = file_paths[f"{ext}_file"]
                file_paths[f"{ext}_file"] = [
                    Path(str(_file)),
                    *(existing if isinstance(existing, list) else [existing]),
                ]
            else:
                file_paths[f"{ext}_file"] = Path(str(_file))
    return file_paths
