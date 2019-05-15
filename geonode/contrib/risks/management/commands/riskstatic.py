# -*- coding: utf-8 -*-
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

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from paver.easy import sh

try:
    from paver.path import pushd
except ImportError:
    from paver.easy import pushd


class Command(BaseCommand):
    """
    This management command allows you to update and recompile the client part of
    this contrib module.

    Example Usage:
    $> python manage.py riskstatic

    # To init the submodule
    $> python manage.py riskstatic --full --init

    # To update the submodule
    $> python manage.py riskstatic --full
    """

    help = 'Update and rebuild Risks contrib client files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--full',
            action='store_true',
            dest='full',
            default=False,
            help='Fully rebuild the client static libs.')
        parser.add_argument(
            '-i',
            '--init',
            action='store_true',
            dest='init',
            default=False,
            help='Fully rebuild the client static libs.')
        return parser

    def handle(self, **options):
        full = options.get('full')
        init = options.get('init')

        # risks app
        with pushd('geonode/contrib/risks/client'):
            if full:
                if init:
                    sh('git submodule update --init --recursive')
                else:
                    sh('git submodule update')
                sh('npm install')

            sh('npm run compile')
            sh('mkdir -p ../static/assets/')
            sh('cp -rvv *.json ../static/js/')
            sh('cp -rvv assets/* ../static/assets/')
            sh('cp -rvv dist/* ../static/js/')
            # sh('cp -rvv MapStore2/web/client/translations ../static/assets/')
