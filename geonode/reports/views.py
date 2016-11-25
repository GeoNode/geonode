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
from django import forms
from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from django.db.models import Q
from django.template.response import TemplateResponse
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template import RequestContext

from pprint import pprint

from actstream.models import Action
from geonode.eula.models import AnonDownloader

from geonode.reports.models import DownloadCount
from collections import OrderedDict

def report_layer(request, template='reports/report_layers.html'):
    monthly_count = OrderedDict()
    monthly_list = DownloadCount.objects.filter(chart_group='monthly').order_by('date')
    for eachinlist in monthly_list:
        if eachinlist.date.strftime('%b') not in monthly_count:
            monthly_count [eachinlist.date.strftime('%b')] = {}
        monthly_count[eachinlist.date.strftime('%b')][eachinlist.download_type] = eachinlist.count
    pprint(monthly_count)

    context_dict = {
        "monthly_count": monthly_count,
    }
    return render_to_response(template, RequestContext(request, context_dict))
