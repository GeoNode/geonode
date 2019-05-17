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

from django.db.models import Q

from geonode.base.models import TopicCategory
from geonode.contrib.risks.models import RiskAnalysis, RiskApp
from geonode.contrib.risks.models import HazardSet, PointOfContact
from geonode.contrib.risks.models import Region, AdministrativeDivision

import xlrd


class Command(BaseCommand):
    """
    Insert or update Metadata for a Risk Analysis.
    It requires as inputs an existing Risk Analysis and the XLSX Metadata file.

    Example Usage:
    $> python manage.py importriskmetadata -r Afghanistan \
        -k "WP6_future_proj_Hospital" \
        -x WP6__Impact_analysis_results_future_projections_Hospital\ -\ metadata.xlsx
    $> python manage.py importriskmetadata -r Afghanistan \
        -k "WP6_future_proj_Population" \
        -x WP6__Impact_analysis_results_future_projections_Population\ -\ metadata.xlsx
    $> python manage.py importriskmetadata -r Afghanistan \
        -k "WP6_loss_Afg_PML_split" \
        -x WP6\ -\ 2050\ Scenarios\ -...-\ Afghanistan\ PML\ Split\ -\ metadata.xlsx

    """

    help = 'Import Risk Metadata: Loss Impact and Impact Analysis Types.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--commit',
            action='store_true',
            dest='commit',
            default=True,
            help='Commits Changes to the storage.')

        parser.add_argument(
            '-r',
            '--region',
            dest='region',
            help='Destination Region.')
        parser.add_argument(
            '-x',
            '--excel-file',
            dest='excel_file',
            help='Input Risk Metadata Table as XLSX File.')
        parser.add_argument(
            '-k',
            '--risk-analysis',
            dest='risk_analysis',
            help='Name of the Risk Analysis associated to the File.')
        parser.add_argument(
            '-a',
            '--risk-app',
            dest='risk_app',
            # nargs=1,
            default=RiskApp.APP_DATA_EXTRACTION,
            help="Name of Risk App, default: {}".format(RiskApp.APP_DATA_EXTRACTION),
            )


    def handle(self, **options):
        commit = options.get('commit')
        region = options.get('region')
        excel_file = options.get('excel_file')
        risk_analysis = options.get('risk_analysis')
        app_name = options.get('risk_app')
        app = RiskApp.objects.get(name=app_name)

        if region is None:
            raise CommandError("Input Destination Region '--region' \
is mandatory")

        if risk_analysis is None:
            raise CommandError("Input Risk Analysis associated to the File \
'--risk_analysis' is mandatory")

        if not excel_file or len(excel_file) == 0:
            raise CommandError("Input Risk Metadata Table '--excel_file' \
is mandatory")

        wb = xlrd.open_workbook(filename=excel_file)
        risk = RiskAnalysis.objects.get(name=risk_analysis, app=app)
        region = Region.objects.get(name=region)
        # region_code = region.administrative_divisions.filter(parent=None)[0].code

        """
        Assuming the following metadata model:

        Section 1: Identification
         Title  	                     [M]
         Date  	                         [M]
         Date Type                       [M]
         Edition  	                     [O]
         Abstract  	                     [M]
         Purpose  	                     [O]
        Section 2: Point of Contact
         Individual Name  	             [M]
         Organization Name               [M]
         Position Name  	             [O]
         Voice  	                     [O]
         Facsimile  	                 [O]
         Delivery Point  	             [O]
         City  	                         [O]
         Administrative Area             [O]
         Postal Code  	                 [O]
         Country  	                     [O]
         Electronic Mail Address  	     [O]
         Role  	                         [M]
         Maintenance & Update Frequency  [O]
        Section 3: Descriptive Keywords
         Keyword  	                     [O]
         Country & Regions  	         [M]
         Use constraints  	             [M]
         Other constraints  	         [O]
         Spatial Representation Type  	 [O]
        Section 4: Equivalent Scale
         Language  	                     [M]
         Topic Category Code  	         [M]
        Section 5: Temporal Extent
         Begin Date  	                 [O]
         End Date  	                     [O]
         Geographic Bounding Box  	     [M]
         Supplemental Information  	     [M]
        Section 6: Distribution Info
         Online Resource  	             [O]
         URL  	                         [O]
         Description  	                 [O]
        Section 7: Reference System Info
         Code  	                         [O]
        Section8: Data quality info
         Statement	                     [O]
        Section 9: Metadata Author
         Individual Name  	             [M]
         Organization Name  	         [M]
         Position Name  	             [O]
         Voice  	                     [O]
         Facsimile  	                 [O]
         Delivery Point  	             [O]
         City  	                         [O]
         Administrative Area  	         [O]
         Postal Code  	                 [O]
         Country  	                     [O]
         Electronic Mail Address  	     [O]
         Role  	                         [O]
        """
        sheet = wb.sheet_by_index(0)

        hazardsets = HazardSet.objects.filter(riskanalysis=risk, country=region)
        if len(hazardsets) > 0:
            hazardset = hazardsets[0]
        else:
            hazardset = HazardSet()

        d = {}
        for row_num in range(0, sheet.nrows):
            cell_title = sheet.cell_value(row_num, 0).strip()
            cell_obj = sheet.cell(row_num, 2)
            if cell_title and 'Section' not in cell_title:
                cell_id = row_num
                cell_value = cell_obj.value.strip()
                d[cell_id] = cell_value
                print("[%s] (%s) %s: %s" % (row_num, cell_title, d[row_num], cell_value))

        # Create or Update the HazardSet
        hazardset.riskanalysis = risk
        hazardset.country = region

        hazardset.title = d[1]
        hazardset.date = d[2]
        hazardset.date_type = d[3]
        hazardset.edition = d[4]
        hazardset.abstract = d[5]
        hazardset.purpose = d[6]
        hazardset.keyword = d[22]
        hazardset.use_contraints = d[24]
        hazardset.other_constraints = d[25]
        hazardset.spatial_representation_type = d[26]
        hazardset.language = d[28]
        hazardset.begin_date = d[31]
        hazardset.end_date = d[32]
        hazardset.bounds = d[33]
        hazardset.supplemental_information = d[34]
        hazardset.online_resource = d[36]
        hazardset.url = d[37]
        hazardset.description = d[38]
        hazardset.reference_system_code = d[40]
        hazardset.data_quality_statement = d[42]

        # Topic Category
        if d[29]:
            values = d[29].split(",")
            for value in values:
                value = value.strip()
                value = value[:-1] if value.endswith(";") or value.endswith("s") else value
                topic_category = \
                    TopicCategory.objects.filter(Q(identifier__icontains=value) | Q(description__icontains=value))
                if len(topic_category) > 0:
                    hazardset.topic_category = topic_category[0]

        # Point Of Contact
        (poc, created) = PointOfContact.objects.get_or_create(individual_name=d[8], organization_name=d[9])
        poc.position_name = d[10]
        poc.voice = d[11]
        poc.facsimile = d[12]
        poc.delivery_point = d[13]
        poc.city = d[14]
        poc.postal_code = d[16]
        poc.e_mail = d[18]
        poc.role = d[19]
        poc.update_frequency = d[20]

        # Relationships
        if d[15]:
            poc_adm = AdministrativeDivision.objects.filter(name=d[15])
            if len(poc_adm) > 0:
                poc.administrative_area = poc_adm[0]

        if d[17]:
            poc_ctry = Region.objects.filter(name=d[17])
            if len(poc_ctry) > 0:
                poc.country = poc_ctry[0]
        hazardset.poc = poc

        # Metadata Author
        author, created = PointOfContact.objects.get_or_create(individual_name=d[44], organization_name=d[45])
        author.position_name = d[46]
        author.voice = d[47]
        author.facsimile = d[48]
        author.delivery_point = d[49]
        author.city = d[50]
        author.postal_code = d[52]
        author.e_mail = d[54]
        author.role = d[55]

        # Relationships
        if d[51]:
            poc_adm = AdministrativeDivision.objects.filter(name=d[51])
            if len(poc_adm) > 0:
                author.administrative_area = poc_adm[0]

        if d[53]:
            poc_ctry = Region.objects.filter(name=d[53])
            if len(poc_ctry) > 0:
                author.country = poc_ctry[0]
        hazardset.author = author
        hazardset.save()

        # Finalize
        risk.hazardset = hazardset
        risk.metadata_file = excel_file
        if commit:
            risk.save()

        return risk_analysis
