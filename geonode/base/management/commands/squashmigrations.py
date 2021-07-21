#########################################################################
#
# Copyright (C) 2017 OSGeo
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
"""
A squashmigrations command which does some monkeypatching on the RunPython operation
to allow squashing migrations which use RunPython.noop, even on Python 2
"""
from django.core.management.commands.squashmigrations import Command as DjangoCommand
from django.db.migrations import RunPython


# A staticmethod decorator is needed (out of a class!) because we are going to
# monkeypatch this function into a class and it will be introspected by code that
# will think it is an unbound instance method without the decorator.
@staticmethod
def noop(apps, schema_editor):
    return None


class Command(DjangoCommand):

    def handle(self, **options):
        # Monkeypatch
        RunPython.noop = noop
        # Invoke original
        return super().handle(**options)
