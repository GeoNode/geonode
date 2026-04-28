#########################################################################
#
# Copyright (C) 2026 OSGeo
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

from abc import ABC, abstractmethod
from typing import Iterable, Mapping


class ValidationConfigProvider(ABC):
    """
    Source of FileValidationUploadHandler config for one or more URL names.

    Implementations declare which URL names they cover (``url_names``) and
    return the merged validation config in ``build_config``. The dict shape
    matches what FileValidationUploadHandler expects:

        {
            "allowed_extensions": frozenset[str],
            "magic_mimetype_map": dict[str, frozenset[str]],
            "magic_description_map": dict[str, frozenset[str]],  # optional
        }

    Either ``magic_mimetype_map`` or ``magic_description_map`` (or both) must
    cover every extension listed in ``allowed_extensions``; otherwise the
    upload handler will reject any upload of that type as "unconfigured".
    """

    @abstractmethod
    def url_names(self) -> Iterable[str]:
        """URL names (i.e. ``request.resolver_match.url_name`` values) this provider serves."""

    @abstractmethod
    def build_config(self) -> Mapping:
        """Return the validation config dict for the URL names above."""
