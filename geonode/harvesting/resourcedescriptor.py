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

import dataclasses
import datetime as dt
import typing
import uuid

from django.contrib.gis import geos


@dataclasses.dataclass()
class RecordDescriptionContact:
    role: str
    name: typing.Optional[str]
    organization: typing.Optional[str]
    position: typing.Optional[str]
    phone_voice: typing.Optional[str]
    phone_facsimile: typing.Optional[str]
    address_delivery_point: typing.Optional[str]
    address_city: typing.Optional[str]
    address_administrative_area: typing.Optional[str]
    address_postal_code: typing.Optional[str]
    address_country: typing.Optional[str]
    address_email: typing.Optional[str]


@dataclasses.dataclass()
class RecordIdentification:
    name: str
    title: str
    date: dt.datetime
    date_type: str
    abstract: typing.Optional[str]
    purpose: typing.Optional[str]
    status: typing.Optional[str]
    originator: RecordDescriptionContact
    graphic_overview_uri: str
    native_format: str
    place_keywords: typing.List[str]
    other_keywords: typing.Tuple
    license: typing.List[str]
    other_constraints: typing.Optional[str]
    topic_category: typing.Optional[str]
    spatial_extent: typing.Optional[geos.Polygon]
    temporal_extent: typing.Optional[typing.Tuple[dt.datetime, dt.datetime]]
    supplemental_information: typing.Optional[str]


@dataclasses.dataclass()
class RecordDistribution:
    link_url: typing.Optional[str]
    wms_url: typing.Optional[str]
    wfs_url: typing.Optional[str]
    wcs_url: typing.Optional[str]
    thumbnail_url: typing.Optional[str]
    legend_url: typing.Optional[str]
    geojson_url: typing.Optional[str]
    original_format_url: typing.Optional[str]


@dataclasses.dataclass()
class RecordDescription:
    uuid: uuid.UUID
    language: typing.Optional[str]
    character_set: typing.Optional[str]
    hierarchy_level: str
    point_of_contact: RecordDescriptionContact
    author: RecordDescriptionContact
    date_stamp: dt.datetime
    reference_system: str
    identification: RecordIdentification
    distribution: RecordDistribution
    data_quality: str
