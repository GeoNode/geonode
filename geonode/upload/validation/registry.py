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

"""
Process-wide registry of upload validation configurations.

Configs are produced by ValidationConfigProvider classes listed in
settings.FILE_VALIDATION_CONFIGURATION_PROVIDERS. They are merged once at
app-ready time (see geonode.upload.handlers.apps.run_setup_hooks) and frozen
into an immutable mapping that FileValidationUploadHandler reads on every
request.

Tests that swap providers should call ``FileValidationConfigRegistry.rebuild()``
explicitly; we deliberately do not subscribe to setting_changed signals to
keep the runtime model simple.

The class mirrors the BaseHandler pattern in geonode.upload.handlers.base:
class-level state, classmethods for mutation/lookup, no instances.
"""

import logging
from types import MappingProxyType
from typing import Iterable, Mapping, Optional

from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class FileValidationConfigRegistry:
    """
    Singleton-style registry of FileValidationUploadHandler configs.

    Mirrors ``geonode.upload.handlers.base.BaseHandler``: class-level state,
    classmethods for installation and lookup, no instantiation.
    """

    REGISTRY: Mapping[str, Mapping] = MappingProxyType({})

    @classmethod
    def install(cls, configs: Mapping[str, Mapping]) -> None:
        """
        Replace the registry with a frozen copy of ``configs``. Called once
        from HandlersConfig.ready() after all providers have run.
        """
        cls.REGISTRY = MappingProxyType({url_name: MappingProxyType(dict(cfg)) for url_name, cfg in configs.items()})
        logger.info(
            "FileValidation registry installed for URL names: %s",
            ", ".join(sorted(cls.REGISTRY)) or "<none>",
        )

    @classmethod
    def get(cls, url_name: Optional[str]) -> Optional[Mapping]:
        """Return the validation config for ``url_name`` or None."""
        if not url_name:
            return None
        return cls.REGISTRY.get(url_name)

    @classmethod
    def rebuild(cls, provider_paths: Optional[Iterable[str]] = None) -> None:
        """
        Re-run providers and refresh the registry.

        Pass ``provider_paths`` to use a specific list (handy for tests).
        When omitted the function reads
        ``settings.FILE_VALIDATION_CONFIGURATION_PROVIDERS``.
        """
        from django.conf import settings

        if provider_paths is None:
            provider_paths = getattr(settings, "FILE_VALIDATION_CONFIGURATION_PROVIDERS", ())

        merged: dict = {}
        for path in provider_paths:
            provider_cls = import_string(path)
            provider = provider_cls()
            cfg = provider.build_config()
            if not cfg:
                continue
            for url_name in provider.url_names():
                if url_name in merged:
                    logger.warning(
                        "FileValidation provider %s overrides existing config for %r",
                        path,
                        url_name,
                    )
                merged[url_name] = cfg
        cls.install(merged)

    @classmethod
    def clear(cls) -> None:
        """Reset the registry to empty. Test helper."""
        cls.install({})
