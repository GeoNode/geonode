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
from . import models


def get_favorite_info(user, content_object):
    """
    return favorite info dict containing:
        a. an add favorite url for the input parameters.
        b. whether there is an existing Favorite for the input parameters.
        c. a delete url (if there is an existing Favorite).
    """
    result = {}

    url_content_type = type(content_object).__name__.lower()
    result["add_url"] = reverse(f"add_favorite_{url_content_type}", args=[content_object.pk])

    existing_favorite = models.Favorite.objects.favorite_for_user_and_content_object(user, content_object)

    if existing_favorite:
        result["has_favorite"] = "true"
        result["delete_url"] = reverse("delete_favorite", args=[existing_favorite.pk])
    else:
        result["has_favorite"] = "false"

    return result
