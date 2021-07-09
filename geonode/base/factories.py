# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2021 Open Source Geospatial Foundation - all rights reserved
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

from django.contrib.auth import get_user_model

import factory

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"Username {n+1}")
    email = factory.Sequence(lambda n: f"email{n+1}@geonodetests.com")


class LayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Layer

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Layer {n+1}")

    @factory.post_generation
    def keywords(self, create, extracted, **kwargs):
        if not create:
            # Simple build strategy.
            return

        if extracted:
            # Use the passed in list
            for keyword in extracted:
                self.keywords.add(keyword)


class MapFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Map

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Map {n+1}")
    zoom = 0
    center_x = 0.0
    center_y = 0.0

    @factory.post_generation
    def keywords(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for keyword in extracted:
                self.keywords.add(keyword)


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Document {n+1}")

    @factory.post_generation
    def keywords(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for keyword in extracted:
                self.keywords.add(keyword)
