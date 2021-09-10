# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django.urls import reverse

from geonode.base.models import ResourceBase
from geonode.tests.base import GeoNodeBaseTestSupport


class MetadataXSLTest(GeoNodeBaseTestSupport):

    """
    Tests geonode.catalogue.metadataxsl app/module
    """

    def setUp(self):
        super(MetadataXSLTest, self).setUp()
        self.adm_un = "admin"
        self.adm_pw = "admin"

    def test_showmetadata_access_perms(self):
        _dataset = ResourceBase.objects.first()
        _dataset.set_permissions({"users": {}, "groups": {}})
        _dataset.save()
        self.client.login(username=self.adm_un, password=self.adm_pw)
        url = reverse('prefix_xsl_line', kwargs={'id': _dataset.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
