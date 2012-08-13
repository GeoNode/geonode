#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from django.contrib.auth.models import User

from geonode import GeoNodeException


def get_default_user():
    """Create a default user
    """
    superusers = User.objects.filter(is_superuser=True).order_by('id')
    if superusers.count() > 0:
        # Return the first created superuser
        return superusers[0]
    else:
        raise GeoNodeException('You must have an admin account configured '
                               'before importing data. '
                               'Try: django-admin.py createsuperuser')


def get_valid_user(user=None):
    """Gets the default user or creates it if it does not exist
    """
    if user is None:
        theuser = get_default_user()
    elif isinstance(user, basestring):
        theuser = User.objects.get(username=user)
    elif user.is_anonymous():
        raise GeoNodeException('The user uploading files must not '
                               'be anonymous')
    else:
        theuser = user

    #FIXME: Pass a user in the unit tests that is not yet saved ;)
    assert isinstance(theuser, User)

    return theuser
