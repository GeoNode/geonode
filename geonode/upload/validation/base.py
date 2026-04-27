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


def merge_handler_configs(handler_classes: Iterable[type]) -> dict:
    """
    Walk a list of importer handler classes and merge their per-handler
    ``upload_validation_config`` into a single FileValidation-ready dict.

    Per-handler shape (one entry per supported extension)::

        {
            "shp": {"description_contains": {"ESRI Shapefile"}},
            "xml": {"mimes": {"application/xml", "text/xml"}},
            "sld": {
                "mimes": {"text/plain", "application/xml", "text/xml"},
                "description_contains": {"XML"},  # optional
            },
        }

    Multiple handlers may declare the same extension; the union of
    ``mimes`` / ``description_contains`` sets is taken.
    """
    allowed: set = set()
    mimes: dict = {}
    descriptions: dict = {}
    for cls in handler_classes:
        cfg = _get_validation_config(cls)
        if not cfg:
            continue
        for ext, rules in cfg.items():
            allowed.add(ext)
            if "mimes" in rules:
                mimes.setdefault(ext, set()).update(rules["mimes"])
            if "description_contains" in rules:
                descriptions.setdefault(ext, set()).update(rules["description_contains"])
    return {
        "allowed_extensions": frozenset(allowed),
        "magic_mimetype_map": {ext: frozenset(s) for ext, s in mimes.items() if s},
        "magic_description_map": {ext: frozenset(s) for ext, s in descriptions.items() if s},
    }


def _get_validation_config(handler_cls: type) -> Mapping:
    """
    Read ``upload_validation_config`` from a handler class.

    Tries the class first (so handlers can declare it as a class attribute);
    falls back to instantiating, mirroring the convention used for
    ``supported_file_extension_config``.
    """
    cfg = getattr(handler_cls, "upload_validation_config", None)
    if isinstance(cfg, (dict, Mapping)):
        return cfg
    try:
        return getattr(handler_cls(), "upload_validation_config", {}) or {}
    except Exception:
        return {}
