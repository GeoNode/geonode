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

# DOCUMENT_TYPE_MAP and DOCUMENT_MIMETYPE_MAP
# match values in settings.ALLOWED_DOCUMENT_TYPES

DOCUMENT_TYPE_MAP = {
    'txt': 'text',
    'log': 'text',
    'doc': 'text',
    'docx': 'text',
    'ods': 'text',
    'odt': 'text',
    'sld': 'text',
    'qml': 'text',
    'xls': 'text',
    'xlsx': 'text',
    'xml': 'text',

    'gif': 'image',
    'jpg': 'image',
    'jpeg': 'image',
    'png': 'image',
    'tif': 'image',
    'tiff': 'image',

    'odp': 'presentation',
    'ppt': 'presentation',
    'pptx': 'presentation',
    'pdf': 'presentation',

    'rar': 'archive',
    'gz': 'archive',
    'zip': 'archive',
}


DOCUMENT_MIMETYPE_MAP = {
    'txt': 'text/plain',
    'log': 'text/plain',
    'doc': 'text/plain',
    'docx': 'text/plain',
    'ods': 'text/plain',
    'odt': 'text/plain',
    'sld': 'text/plain',
    'qml': 'text/plain',
    'xls': 'text/plain',
    'xlsx': 'text/plain',
    'xml': 'text/xml',

    'gif': 'image/gif',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',

    'odp': 'text/plain',
    'ppt': 'text/plain',
    'pptx': 'text/plain',
    'pdf': 'application/pdf',

    'rar': 'application/x-rar-compressed',
    'gz': 'application/x-gzip',
    'zip': 'application/zip',
}
