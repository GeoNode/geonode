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
import os
import ast

from django.conf import settings

_DEFAULT_REGISTERED_MEMBERS_GROUP_NAME = os.getenv(
    'REGISTERED_MEMBERS_GROUP_NAME', 'registered-members')

_DEFAULT_REGISTERED_MEMBERS_GROUP_TITLE = os.getenv(
    'REGISTERED_MEMBERS_GROUP_TITLE', 'Registered Members')

_DEFAULT_AUTO_ASSIGN_REGISTERED_MEMBERS_TO = ast.literal_eval(
    os.getenv('AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', 'True'))

# options: "registration" | "activation" | "login"
_DEFAULT_AUTO_ASSIGN_REGISTERED_MEMBERS_AT = os.getenv(
    'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT', 'activation')

try:
    REGISTERED_MEMBERS_GROUP_NAME = getattr(
        settings, 'REGISTERED_MEMBERS_GROUP_NAME', _DEFAULT_REGISTERED_MEMBERS_GROUP_NAME)
except AttributeError:
    REGISTERED_MEMBERS_GROUP_NAME = _DEFAULT_REGISTERED_MEMBERS_GROUP_NAME

try:
    REGISTERED_MEMBERS_GROUP_TITLE = getattr(
        settings, 'REGISTERED_MEMBERS_GROUP_TITLE', _DEFAULT_REGISTERED_MEMBERS_GROUP_TITLE)
except AttributeError:
    REGISTERED_MEMBERS_GROUP_TITLE = _DEFAULT_REGISTERED_MEMBERS_GROUP_TITLE

AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME = getattr(
    settings, 'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME',
    _DEFAULT_AUTO_ASSIGN_REGISTERED_MEMBERS_TO)

AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT = getattr(
    settings, 'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT',
    _DEFAULT_AUTO_ASSIGN_REGISTERED_MEMBERS_AT)
