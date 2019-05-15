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

from django.core.management.base import BaseCommand, CommandError
from geonode.layers.models import Layer
from geonode.contrib.risks.models import RiskAnalysis, HazardType, RiskApp
from geonode.contrib.risks.models import AnalysisType, DymensionInfo
from geonode.contrib.risks.models import RiskAnalysisDymensionInfoAssociation

import ConfigParser

Config = ConfigParser.ConfigParser()

RISK_APPS = [a[0] for a in RiskApp.APPS]
RISK_APP_DEFAULT = RiskApp.APP_DATA_EXTRACTION

class Command(BaseCommand):
    """
    Allows to define a new Risk Analysis along with Dymentions descriptors.

    The command needs an 'ini' file defined as follows (just an example):

        [DEFAULT]
        # optional, if not provided, data_extraction will be used 
        # (or any other provided in -r cli switch)
        app = data_extraction|cost_benefit_analysis

        # unique and less than 30 characters
        name = future_projections_Hospital

        # can be 'impact' or 'loss_impact'
        analysis_type = impact

        # must use mnemonics
        hazard_type = EQ

        # must exists on GeoNode and you have to use its native 'name'
        # **not** the title
        layer = test

        [DIM1]
        # can be 'Scenario' or 'Round Period' for now
        dymensioninfo = Scenario

        # the first one must be always the baseline; the order is important
        values =
            Hospital
            SSP1
            SSP2
            SSP3
            SSP4
            SSP5

        # can be 'x', 'y', 'z', 't', 'e'; the order is important
        #  - layer 'x' always corresponds to the XLSX sheets
        #  - layer 'y' always corresponds to the XLSX columns
        axis = x

        # corresponding attribute name of the 'layer'
        layer_attribute = dim1

        [DIM2]
        # can be 'Scenario' or 'Round Period' for now
        dymensioninfo = Round Period

        # the first one must be always the baseline; the order is important
        values =
            10
            20
            50
            100
            250
            500
            1000
            2500

        # can be 'x', 'y', 'z', 't', 'e'; the order is important
        #  - layer 'x' always corresponds to the XLSX sheets
        #  - layer 'y' always corresponds to the XLSX columns
        axis = y

        # corresponding attribute name of the 'layer'
        layer_attribute = dim2

    Example Usage:
    $> python manage.py createriskanalysis \
            -f WP6__Impact_analysis_results_future_projections_Hospital.ini
    $> python manage.py createriskanalysis \
            -f WP6__Impact_analysis_results_future_projections_Population.ini
    $> python manage.py createriskanalysis \
            -f WP6\ -\ 2050\ Scenarios\ -\ ...\ Afghanistan\ PML\ Split.ini

    """

    help = 'Creates a new Risk Analysis descriptor: \
Loss Impact and Impact Analysis Types.'


    def add_arguments(self, parser):
        parser.add_argument('-f',
                            '--descriptor-file',
                            dest='descriptor_file',
                            type=str,
                            help='Input Risk Analysis Descriptor INI File.')
        parser.add_argument('-a',
                            '--risk-app',
                            dest='risk_app',
                            default=RISK_APP_DEFAULT,
                            help="Risk application name, available: {}, default: {}. Note that app config value has precedense over cli switch.".format(', '.join(RISK_APPS), RISK_APP_DEFAULT)
                            )

        return parser

    def handle(self, **options):
        descriptor_file = options.get('descriptor_file')

        if not descriptor_file or len(descriptor_file) == 0:
            raise CommandError("Input Risk Analysis Descriptor INI File \
'--descriptor_file' is mandatory")

        Config.read(descriptor_file)
        risk_name = Config.get('DEFAULT', 'name')
        analysis_type_name = Config.get('DEFAULT', 'analysis_type')
        hazard_type_name = Config.get('DEFAULT', 'hazard_type')
        layer_name = Config.get('DEFAULT', 'layer')
        try:
            app_name = Config.get('DEFAULT', 'app')
        except ConfigParser.NoOptionError:
            app_name = options['risk_app']

        app = RiskApp.objects.get(name=app_name)

        if RiskAnalysis.objects.filter(name=risk_name, app=app).exists():
            raise CommandError("A Risk Analysis with name '" + risk_name +
                               "' already exists on DB!")

        if not HazardType.objects.filter(mnemonic=hazard_type_name, app=app).exists():
            raise CommandError("An Hazard Type with mnemonic '" +
                               hazard_type_name+"' does not exist on DB!")

        if not AnalysisType.objects.filter(name=analysis_type_name, app=app).exists():
            raise CommandError("An Analysis Type with name '" +
                               analysis_type_name + "' does not exist on DB!")

        if not Layer.objects.filter(name=layer_name).exists():
            raise CommandError("A Layer with name '" + layer_name +
                               "' does not exist on DB!")

        hazard = HazardType.objects.get(mnemonic=hazard_type_name, app=app)
        analysis = AnalysisType.objects.get(name=analysis_type_name, app=app)
        layer = Layer.objects.get(name=layer_name)

        risk = RiskAnalysis(name=risk_name, app=app)
        risk.analysis_type = analysis
        risk.hazard_type = hazard
        risk.layer = layer
        risk.save()
        risk.set_queued()
        print ("Created Risk Analysis [%s] (%s) - %s" %
               (risk_name, hazard, analysis))

        for section in Config.sections():
            dimension_values = ConfigSectionMap(section)

            values = list(filter(None,
                                 (x.strip() for x in
                                  dimension_values['values'].splitlines())))

            dim_name = dimension_values['dymensioninfo']
            for counter, dim_value in enumerate(values):
                rd = RiskAnalysisDymensionInfoAssociation(value=dim_value)
                rd.dymensioninfo = DymensionInfo.objects.get(name=dim_name)
                rd.riskanalysis = risk
                rd.order = counter
                rd.axis = dimension_values['axis']
                rd.layer_attribute = dimension_values['layer_attribute']
                rd.save()
                print ("Created Risk Analysis Dym %s [%s] (%s) - axis %s" %
                       (rd.order, dim_value, dim_name, rd.axis))
        risk.save()
        risk.set_ready()
        return risk_name


def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1
