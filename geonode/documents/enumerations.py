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
    "log": "text",
    "doc": "text",
    "docx": "text",
    "ods": "text",
    "odt": "text",
    "sld": "text",
    "qml": "text",
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
    "tar": "archive",
    "tgz": "archive",
    "rar": "archive",
    "gz": "archive",
    "7z": "archive",
    "zip": "archive",
    "aif": "audio",
    "aifc": "audio",
    "aiff": "audio",
    "au": "audio",
    "mp3": "audio",
    "mpga": "audio",
    "wav": "audio",
    "afl": "video",
    "avi": "video",
    "avs": "video",
    "fli": "video",
    "mp2": "video",
    "mp4": "video",
    "mpg": "video",
    "ogg": "video",
    "webm": "video",
    "3gp": "video",
    "flv": "video",
    "vdo": "video",
}


DOCUMENT_MIMETYPE_MAP = {
    "txt": "text/plain",
    "log": "text/plain",
    "doc": "application/msword",
    "docx": "application/msword",
    "ods": "text/plain",
    "odt": "text/plain",
    "sld": "text/plain",
    "qml": "text/plain",
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
    "tar": "application/x-tar",
    "tgz": "application/x-compressed",
    "rar": "application/x-rar-compressed",
    "gz": "application/x-gzip",
    "7z": "application/zip",
    "zip": "application/zip",
    "aif": "audio/aiff",
    "aifc": "audio/aiff",
    "aiff": "audio/aiff",
    "au": "audio/basic",
    "mp3": "audio/mp3",
    "mpga": "audio/mpeg",
    "wav": "audio/wav",
    "afl": "video/animaflex",
    "avi": "video/avi",
    "avs": "video/avs-video",
    "fli": "video/fli",
    "mp2": "video/mpeg",
    "mp4": "video/mp4",
    "mpg": "video/mpeg",
    "ogg": "video/ogg",
    "webm": "video/webm",
    "3gp": "video/3gp",
    "flv": "video/flv",
    "vdo": "video/vdo",
}
