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
            monthly_count[eachinlist.date.strftime('%b')] = {}
        try: #because of keyerror
        # if len(monthly_count) > 1:
            cumulative_count = monthly_count[monthly_count.keys()[-2]][eachinlist.download_type] + eachinlist.count
        except:
        # else:
            cumulative_count = eachinlist.count
        if eachinlist.download_type in monthly_count[eachinlist.date.strftime('%b')]:
            monthly_count[eachinlist.date.strftime('%b')][eachinlist.download_type] += eachinlist.count
        else:
            monthly_count[eachinlist.date.strftime('%b')][eachinlist.download_type] = cumulative_count
    pprint(monthly_count)

    reversed_mc = OrderedDict(reversed(list(monthly_count.items())))

    luzvimin_count = OrderedDict()
    luzvimin_list = DownloadCount.objects.filter(chart_group='luzvimin').order_by('date')
    for eachinlist in luzvimin_list:
        if eachinlist.date.strftime('%b') not in luzvimin_count:
            luzvimin_count[eachinlist.date.strftime('%b')] = {}
        if eachinlist.category not in luzvimin_count[eachinlist.date.strftime('%b')]:
            luzvimin_count[eachinlist.date.strftime('%b')][eachinlist.category] = 0
        luzvimin_count[eachinlist.date.strftime('%b')][eachinlist.category] += eachinlist.count

        luzvimin_count[eachinlist.date.strftime('%b')]

    reversed_luzvimin = OrderedDict(reversed(list(luzvimin_count.items())))
    context_dict = {
        "monthly_count": reversed_mc,
        "luzvimin_count": reversed_luzvimin,
    }
    pprint(luzvimin_count)
    return render_to_response(template, RequestContext(request, context_dict))
