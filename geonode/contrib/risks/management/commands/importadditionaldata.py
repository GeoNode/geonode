#!/usr/bin/env python
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


from optparse import make_option

from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError

from geonode.contrib.risks.models import RiskAnalysis, AdditionalData


class Command(BaseCommand):
    """
    Imports additional data tables from spreadsheets.

    """

    def add_arguments(self, parser):

        parser.add_argument('risk',
                            nargs=1,
                            help="Name or id of risk analysis")
        parser.add_argument('sheet_file',
                            nargs=1,
                            help="Path to spreasheet file")


        return parser


    def handle(self, **options):
        risk_name = options['risk'][0]
        sheet_file = options['sheet_file'][0]

        try:
            risk_id = int(risk_name)
        except (TypeError, ValueError,):
            risk_id = None
        if risk_id is None:
            q = Q(name=risk_name)
        else:
            q = Q(name=risk_name)|Q(id=risk_id)
        try:
            risk = RiskAnalysis.objects.get(q)
        except RiskAnalysis.DoesNotExist:
            raise CommandError("Cannot find risk analysis: {}".format(risk_name))

        ad = AdditionalData.import_from_sheet(risk, sheet_file)
        print("AdditionalData {} added".format(ad))
