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
    name: typing.Optional[str] = ""
    organization: typing.Optional[str] = ""
    position: typing.Optional[str] = ""
    phone_voice: typing.Optional[str] = ""
    phone_facsimile: typing.Optional[str] = ""
    address_delivery_point: typing.Optional[str] = ""
    address_city: typing.Optional[str] = ""
    address_administrative_area: typing.Optional[str] = ""
    address_postal_code: typing.Optional[str] = ""
    address_country: typing.Optional[str] = ""
    address_email: typing.Optional[str] = ""


@dataclasses.dataclass()
class RecordIdentification:
    name: str
    title: str
    date: typing.Optional[dt.datetime] = None
    date_type: typing.Optional[str] = None
    originator: typing.Optional[RecordDescriptionContact] = None
    place_keywords: typing.Optional[typing.List[str]] = None
    other_keywords: typing.Optional[typing.Iterable] = None
    license: typing.Optional[typing.List[str]] = None
    abstract: typing.Optional[str] = ""
    purpose: typing.Optional[str] = ""
    status: typing.Optional[str] = ""
    native_format: typing.Optional[str] = None
    other_constraints: typing.Optional[str] = ""
    topic_category: typing.Optional[str] = None
    supplemental_information: typing.Optional[str] = ""
    spatial_extent: typing.Optional[geos.Polygon] = None
    lonlat_extent: typing.Optional[geos.Polygon] = None
    temporal_extent: typing.Optional[typing.Tuple[dt.datetime, dt.datetime]] = None


@dataclasses.dataclass()
class RecordDistribution:
    link_url: typing.Optional[str] = None
    wms_url: typing.Optional[str] = None
    wfs_url: typing.Optional[str] = None
    wcs_url: typing.Optional[str] = None
    thumbnail_url: typing.Optional[str] = None
    download_url: typing.Optional[str] = None
    embed_url: typing.Optional[str] = None


@dataclasses.dataclass()
class MapDescriptorParameters:
    last_modified: dt.datetime


@dataclasses.dataclass()
class RecordDescription:
    uuid: uuid.UUID
    identification: RecordIdentification
    distribution: RecordDistribution
    point_of_contact: typing.Optional[RecordDescriptionContact] = None
    author: typing.Optional[RecordDescriptionContact] = None
    date_stamp: typing.Optional[dt.datetime] = None
    reference_systems: typing.Optional[typing.List[str]] = None
    data_quality: typing.Optional[str] = None
    additional_parameters: typing.Optional[typing.Dict] = dataclasses.field(default_factory=dict)
    language: typing.Optional[str] = None
    character_set: typing.Optional[str] = None
