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

# DOCUMENT_TYPE_MAP and DOCUMENT_MIMETYPE_MAP
# match values in settings.ALLOWED_DOCUMENT_TYPES

DOCUMENT_TYPE_MAP = {
    "txt": "text",
    "csv": "text",
    "log": "text",
    "doc": "text",
    "docx": "text",
    "ods": "text",
    "odt": "text",
    "sld": "text",
    "xls": "text",
    "xlsx": "text",
    "xml": "text",
    "bm": "image",
    "bmp": "image",
    "dwg": "archive",
    "dxf": "archive",
    "fif": "image",
    "gif": "image",
    "jpg": "image",
    "jpe": "image",
    "jpeg": "image",
    "png": "image",
    "tif": "archive",
    "tiff": "archive",
    "pbm": "archive",
    "odp": "presentation",
    "ppt": "presentation",
    "pptx": "presentation",
    "pdf": "presentation",
    "gz": "archive",
    "zip": "archive",
    "mp3": "audio",
    "wav": "audio",
    "mp4": "video",
    "ogg": "video",
}


DOCUMENT_MIMETYPE_MAP = {
    "txt": "text/plain",
    "csv": "text/plain",
    "log": "text/plain",
    "doc": "application/msword",
    "docx": "application/msword",
    "ods": "text/plain",
    "odt": "text/plain",
    "sld": "text/plain",
    "xls": "application/excel",
    "xlsx": "application/vnd.ms-excel",
    "xml": "application/xml",
    "bm": "image/bmp",
    "bmp": "image/bmp",
    "dwg": "image/vnd.dwg",
    "dxf": "image/vnd.dwg",
    "fif": "image/fif",
    "gif": "image/gif",
    "jpe": "image/jpeg",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "pbm": "image/x-portable-bitmap",
    "odp": "application/odp",
    "ppt": "application/powerpoint",
    "pptx": "application/x-mspowerpoint",
    "pdf": "application/pdf",
    "gz": "application/x-gzip",
    "zip": "application/zip",
    "mp3": "audio/mp3",
    "wav": "audio/wav",
    "mp4": "video/mp4",
    "ogg": "video/ogg",
}


DOCUMENT_MAGIC_MIMETYPE_MAP = {extension: {mime_type} for extension, mime_type in DOCUMENT_MIMETYPE_MAP.items()}
DOCUMENT_MAGIC_MIMETYPE_MAP.update(
    {
        "csv": {"text/plain", "text/csv"},
        "log": {"text/plain", "text/csv"},
        "xml": {"application/xml", "text/xml"},
        "sld": {"text/plain", "application/xml", "text/xml"},
        "dxf": {"image/vnd.dwg", "image/vnd.dxf"},
        "doc": {"application/msword", "application/x-ole-storage"},
        "docx": {
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
        "ods": {"text/plain", "application/vnd.oasis.opendocument.spreadsheet"},
        "odt": {"text/plain", "application/vnd.oasis.opendocument.text"},
        "xls": {"application/excel", "application/vnd.ms-excel", "application/x-ole-storage"},
        "xlsx": {
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
        "odp": {"application/odp", "application/vnd.oasis.opendocument.presentation"},
        "ppt": {"application/powerpoint", "application/vnd.ms-powerpoint", "application/x-ole-storage"},
        "pptx": {
            "application/x-mspowerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        },
        "gz": {"application/gzip", "application/x-gzip"},
        "mp3": {"audio/mp3", "audio/mpeg"},
        "wav": {"audio/wav", "audio/x-wav"},
        "ogg": {"application/ogg", "audio/ogg", "video/ogg"},
    }
)
