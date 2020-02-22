# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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


long, unicode, basestring = int, str, str
unicode = str
string_type = str


def ensure_string(payload_bytes):
    import re
    _payload = payload_bytes
    try:
        _payload = payload_bytes.decode("utf-8")
    except AttributeError:
        # when _payload is already a string
        pass
    except UnicodeDecodeError:
        # when payload is a byte-like object (e.g bytearray)
        # primarily used in when _payload is an image
        return _payload
    if re.match(r'b\'(.*)\'', _payload):
        _payload = re.match(r'b\'(.*)\'', _payload).groups()[0]
    return _payload
