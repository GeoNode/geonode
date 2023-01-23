##############################################
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


import uuid
import datetime
from geonode.harvesting import resourcedescriptor
from geonode.harvesting.harvesters.base import HarvestedResourceInfo, BriefRemoteResource

contact_example = resourcedescriptor.RecordDescriptionContact(role="role", name="Test")
identification_example = resourcedescriptor.RecordIdentification(
    name="Test",
    title="Test",
    date=datetime.datetime.now(),
    date_type="type",
    originator=contact_example,
    place_keywords=["keyword"],
    other_keywords=("test",),
    license=["test"],
)
distribution_example = resourcedescriptor.RecordDistribution()
resource_description_example = resourcedescriptor.RecordDescription(
    uuid=uuid.uuid4(),
    point_of_contact=contact_example,
    author=contact_example,
    date_stamp=datetime.datetime.now(),
    identification=identification_example,
    distribution=distribution_example,
)

resource_info_example = HarvestedResourceInfo(
    resource_descriptor=resource_description_example, additional_information={}
)

brief_remote_resource_example = BriefRemoteResource(
    unique_identifier="id", title="Test", abstract="", resource_type="Layer"
)
