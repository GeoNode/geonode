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
import base64

from geonode.maps.models import Map


def _decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    _thumbnail_format = "png"
    _invalid_padding = data.find(";base64,")
    if _invalid_padding:
        _thumbnail_format = data[data.find("image/") + len("image/"):_invalid_padding]
        data = data[_invalid_padding + len(";base64,"):]
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += b"=" * (4 - missing_padding)
    return (base64.b64decode(data), _thumbnail_format)


def handle_map_thumbnail(thumbnail, map_obj: Map):
    _map_thumbnail = thumbnail or map_obj.thumbnail_url
    _map_thumbnail_format = "png"

    try:
        (_map_thumbnail, _map_thumbnail_format) = _decode_base64(_map_thumbnail)
    except Exception:
        if _map_thumbnail:
            _map_thumbnail_format = "link"

    if _map_thumbnail:
        if _map_thumbnail_format == "link":
            map_obj.thumbnail_url = _map_thumbnail
        else:
            _map_thumbnail_filename = f"map-{map_obj.uuid}-thumb.{_map_thumbnail_format}"
            map_obj.save_thumbnail(_map_thumbnail_filename, _map_thumbnail)
