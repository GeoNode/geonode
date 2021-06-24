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
import factory
import random
import string
import hashlib
from datetime import datetime
from factory.django import DjangoModelFactory

from geonode.br.models import RestoredBackup


def random_md5_hash() -> str:
    """
    Method calculating MD5 hash of a random string

    :return: hex representation of md5 hash of a random string
    """
    return hashlib.md5(
        ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=15)
        ).encode('utf-8')
    ).hexdigest()


class RestoredBackupFactory(DjangoModelFactory):
    class Meta:
        model = RestoredBackup

    name = factory.Faker('word')
    archive_md5 = factory.LazyFunction(random_md5_hash)
    restoration_date = factory.LazyFunction(datetime.now)
    creation_date = factory.Faker('date_time')
