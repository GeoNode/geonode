
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

from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.test import RequestFactory


from geonode.people.models import Profile as User

from geonode.contrib.risks.views import PDFReportView
from geonode.contrib.risks.models import AnalysisType, HazardType, RiskAnalysis, RiskApp
from geonode.contrib.risks import pdf_helpers

class Command(BaseCommand):
    """
    Generates RiskAnalysis pdf report
    """

    def add_arguments(self, parser):
        parser.add_argument('risk_id',
                            nargs=1,
                            help="ID of risk analysis")
        parser.add_argument('location',
                            nargs=1,
                            help="Location code")
        parser.add_argument('pdf_output',
                            nargs=1,
                            help="Result file")

            
    
    def handle(self, **options):
        rid = options['risk_id'][0]
        pdf_output = options['pdf_output'][0]
        loc_code = options['location'][0]

        u = User.objects.get(username='admin')
        r = RiskAnalysis.objects.get(id=rid)
        app = r.app
        ht = r.hazard_type
        at = r.analysis_type
        loc = r.administrative_divisions.get(code=loc_code)
        

        view_kwargs = {'an': str(r.id),
                       'loc': loc.code,
                       #'app': app.name,
                       'ht': ht.mnemonic,
                       'at': at.name}

        rf = RequestFactory()
        pdf_url = app.url_for('pdf_report', **view_kwargs)

        request = rf.get(pdf_url)
        request.user = u

        v = PDFReportView.as_view()
        resp = v(request, **view_kwargs)
        tmpl = resp.render()
        report_view = PDFReportView(request=request, kwargs=view_kwargs)
        ctx = report_view.get_context_data()
        ctx_url = report_view.get_context_url(**view_kwargs)
        html_path = report_view.render_report_markup(ctx_url, request, **view_kwargs)

        #map, chart, legend, pdf_gen_name=None)
        pdf_helpers.generate_pdf(html_path, pdf_output, '', '', '')



