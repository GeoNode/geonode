#########################################################################
#
# Copyright (C) 2025 OSGeo
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

import logging

from geonode.geoserver.helpers import gs_catalog
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class BaseFeatureValidator:
    """
    Base class for feature validators.
    """

    def __init__(self, dataset):
        self.dataset = dataset

    def validate(self, feature):
        """
        Validates the feature.
        Should raise an exception if validation fails.
        """
        raise NotImplementedError


class GeoserverFeatureValidator(BaseFeatureValidator):
    """
    Validates features against constraints defined in GeoServer's DescribeFeatureType.
    """

    def __init__(self, dataset):
        super().__init__(dataset)
        self.restrictions = {}
        if self.dataset.subtype == "vector":
            feature_type = self._get_feature_type(self.dataset)
            if feature_type:
                self.restrictions = self._get_restrictions(feature_type)

    def validate(self, feature):
        """
        Validates the feature against GeoServer constraints.
        """
        if not self.restrictions:
            return

        errors = []
        for attribute_name, value in feature.items():
            if attribute_name in self.restrictions:
                try:
                    self._validate_attribute(attribute_name, value, self.restrictions[attribute_name])
                except ValidationError as e:
                    if hasattr(e, "messages"):
                        errors.extend(e.messages if isinstance(e.messages, list) else [e.messages])
                    else:
                        errors.append(str(e))
        if errors:
            raise ValidationError(errors)

    def _get_feature_type(self, dataset):
        try:
            return gs_catalog.get_resource(name=dataset.name, store=dataset.store, workspace=dataset.workspace)
        except Exception as e:
            logger.error(f"Error fetching feature type from GeoServer: {e}")
            return None

    def _get_restrictions(self, feature_type):
        return getattr(feature_type, "attributes_restrictions", None)

    def _validate_attribute(self, attribute_name, value, restriction_info):
        if "restrictions" in restriction_info:
            if "enumeration" in restriction_info["restrictions"]:
                self._validate_enumeration(attribute_name, value, restriction_info["restrictions"]["enumeration"])
            if "range" in restriction_info["restrictions"]:
                self._validate_range(attribute_name, value, restriction_info["restrictions"]["range"])

    def _validate_enumeration(self, attribute_name, value, enumeration):
        if str(value) not in enumeration:
            raise ValidationError(
                f'Invalid value for attribute "{attribute_name}". '
                f'Value "{value}" is not in the allowed enumeration: {enumeration}.'
            )

    def _validate_range(self, attribute_name, value, range_info):
        min_val = range_info.get("min")
        max_val = range_info.get("max")
        try:
            value_as_float = float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f'Value "{value}" for attribute "{attribute_name}" is not a valid number for range validation.'
            )
        if min_val is not None and value_as_float < float(min_val):
            raise ValidationError(
                f'Invalid value for attribute "{attribute_name}". '
                f"Value {value} is less than the minimum allowed value of {min_val}."
            )
        if max_val is not None and value_as_float > float(max_val):
            raise ValidationError(
                f'Invalid value for attribute "{attribute_name}". '
                f"Value {value} is greater than the maximum allowed value of {max_val}."
            )
