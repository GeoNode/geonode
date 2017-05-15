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

from geonode.reports.models import DownloadCount, SUCLuzViMin
from collections import OrderedDict, Counter
from geonode.datarequests.models.data_request import DataRequest
from geonode.datarequests.models.profile_request import ProfileRequest
from geonode.people.models import OrganizationType
from geonode.datarequests.models import LipadOrgType

import urllib2, json
from urllib2 import HTTPError
from datetime import datetime
from unidecode import unidecode

def report_distribution_status(request, template='reports/distribution_status.html'):
    #LAYER
    monthly_count = {}
    monthly_list = DownloadCount.objects.filter(chart_group='monthly').order_by('date')
    for eachinlist in monthly_list:
        if eachinlist.date.strftime('%Y%m') not in monthly_count:
            monthly_count[eachinlist.date.strftime('%Y%m')] = {}
        if eachinlist.download_type not in monthly_count[eachinlist.date.strftime('%Y%m')]:
            monthly_count[eachinlist.date.strftime('%Y%m')][eachinlist.download_type] = 0
        monthly_count[eachinlist.date.strftime('%Y%m')][eachinlist.download_type] += int(eachinlist.count)

    luzvimin_count = {'Luzon':{},'Visayas':{},'Mindanao':{},'Others':{}}
    luzvimin_list = DownloadCount.objects.filter(chart_group='luzvimin').order_by('category','date')
    for eachinlist in luzvimin_list:
        try:
            luzvimin = SUCLuzViMin.objects.filter(suc=eachinlist.category)[0].luzvimin
        except:
            luzvimin = 'Others'
        if eachinlist.category=='Luzvimin_others': eachinlist.category='Others'
        if eachinlist.category not in luzvimin_count[luzvimin]:
            luzvimin_count[luzvimin][eachinlist.category] = {}
        if eachinlist.date.strftime('%Y%m') not in luzvimin_count[luzvimin][eachinlist.category]:
            luzvimin_count[luzvimin][eachinlist.category][eachinlist.date.strftime('%Y%m')] = 0
        luzvimin_count[luzvimin][eachinlist.category][eachinlist.date.strftime('%Y%m')] += int(eachinlist.count)

    urls_to_visit = ['https://lipad-fmc.dream.upd.edu.ph/']
#    urls_to_visit = []
    for each_url in urls_to_visit:
        try:
            response = urllib2.urlopen(each_url + 'api/download_count/')
            data = json.loads(response.read())
            objdict = data[u'objects']
            for eachentry in objdict:
                date_of_entry = datetime.strptime(eachentry[u'date'],'%Y-%m-%dT%H:%M:%S').strftime('%Y%m')
                if eachentry[u'chart_group'] == 'monthly':
                    if date_of_entry not in monthly_count:
                        monthly_count[date_of_entry] = {}
                    if eachentry[u'download_type'] not in monthly_count[date_of_entry]:
                        monthly_count[date_of_entry][eachentry[u'download_type']] = 0
                    monthly_count[date_of_entry][eachentry[u'download_type']] += int(eachentry[u'count'])
                elif eachentry[u'chart_group'] == 'luzvimin':
                    try:
                        luzvimin = SUCLuzViMin.objects.filter(suc=eachentry[u'category'])[0].luzvimin
                    except:
                        luzvimin = 'Others'
                    if eachentry[u'category']=='Luzvimin_others': eachentry[u'category']='Others'
                    if eachentry[u'category'] not in luzvimin_count[luzvimin]:
                        luzvimin_count[luzvimin][eachentry[u'category']] = {}
                    if date_of_entry not in luzvimin_count[luzvimin][eachentry[u'category']]:
                        luzvimin_count[luzvimin][eachentry[u'category']][date_of_entry] = 0
                    luzvimin_count[luzvimin][eachentry[u'category']][date_of_entry] += int(eachentry[u'count'])
        except HTTPError:
            continue

    #sorted
    sorted_mc = OrderedDict(sorted(monthly_count.iteritems(), key=lambda x: x[0]))
    #cumulative
    counter_dict = Counter()
    for each in sorted_mc.iteritems():
        counter_dict.update(each[1])
        sorted_mc[each[0]] = dict(counter_dict)
    #rename
    renamed_mc = OrderedDict([(datetime.strptime(eachone[0],'%Y%m').strftime('%b%Y'),eachone[1]) for eachone in sorted_mc.iteritems()])

    reversed_mc = OrderedDict(reversed(list(renamed_mc.items())))

    #DATAREQUEST
    rearrange_dr = {}
    monthly_datarequest = {}
    org_count = {}
    filter_duplicates = []
    monthly_datarequest_list = ProfileRequest.objects.all().order_by('status_changed')
    for eachinlist in monthly_datarequest_list:
        if eachinlist.status_changed.strftime('%Y%m') not in monthly_datarequest:
            monthly_datarequest[eachinlist.status_changed.strftime('%Y%m')] = {}
        if eachinlist.status not in monthly_datarequest[eachinlist.status_changed.strftime('%Y%m')]:
            monthly_datarequest[eachinlist.status_changed.strftime('%Y%m')][eachinlist.status] = 0
        monthly_datarequest[eachinlist.status_changed.strftime('%Y%m')][eachinlist.status] += 1

        if eachinlist.first_name+' '+eachinlist.last_name not in filter_duplicates:
            filter_duplicates.append(eachinlist.first_name+' '+eachinlist.last_name)
            org_type_sub = LipadOrgType.objects.get(val=eachinlist.org_type).category
            if org_type_sub not in org_count:
                org_count[org_type_sub] = 0
            org_count[org_type_sub] += 1



    #sorted
    sorted_md = OrderedDict(sorted(monthly_datarequest.iteritems(), key=lambda x: x[0]))
    sorted_org = OrderedDict(sorted(org_count.iteritems(), key=lambda x: x[0]))
    #cumulative
    counter_dict = Counter()
    for each in sorted_md.iteritems():
        counter_dict.update(each[1])
        sorted_md[each[0]] = dict(counter_dict)
    sorted_luzvimin = OrderedDict([('Luzon',OrderedDict()),('Visayas',OrderedDict()),('Mindanao',OrderedDict()),('Others',OrderedDict())])
    total_luzvimin = OrderedDict([('Luzon',OrderedDict()),('Visayas',OrderedDict()),('Mindanao',OrderedDict()),('Others',OrderedDict())])
    for chart_group, sucdatevalue in luzvimin_count.iteritems():
        date_list = []
        for suc in sorted(sucdatevalue):
            for date in sorted(sucdatevalue[suc]):
                if date not in date_list:
                    date_list.append(date)
        for suc in sorted(sucdatevalue):
            sorted_luzvimin[chart_group][suc]=OrderedDict()
            cumulative_value = 0
            for date in sorted(date_list):
                if date in sucdatevalue[suc].keys():
                    cumulative_value += int(sucdatevalue[suc][date])
                sorted_luzvimin[chart_group][suc][datetime.strptime(date,'%Y%m').strftime('%b%Y')] = cumulative_value
                total_luzvimin[chart_group].update({suc:cumulative_value})
    #rename
    renamed_md = OrderedDict([(datetime.strptime(eachone[0],'%Y%m').strftime('%b%Y'),eachone[1]) for eachone in sorted_md.iteritems()])
    # converts num to OrganizationType Choices
    # renamed_org = OrderedDict([(OrganizationType.get(eachone[0]),eachone[1]) for eachone in sorted_org.iteritems()])
    reversed_md = OrderedDict(reversed(list(renamed_md.items())))
    reversed_org = OrderedDict(reversed(list(sorted_org.items())))
    color_list = ['FF3333','FF9900','F2DB00','00CC66','0099FF','3BB9C4','D4502F','C2C14C','9865CF','D19E45']
    context_dict = {
        "monthly_count": reversed_mc,
        "luzvimin_count": sorted_luzvimin,
        "total_luzvimin": total_luzvimin,
        "total_layers": reversed_mc[reversed_mc.keys()[0]],
        "sum_layers": sum(reversed_mc[reversed_mc.keys()[0]].values()),
        "monthly_datarequest": reversed_md,
        "org_count": reversed_org,
        "total_datarequest": reversed_md[reversed_md.keys()[0]],
        "sum_org_count": sum(org_count.values()),
        "sum_datarequest": sum(reversed_md[reversed_md.keys()[0]].values()),
        "color_list": color_list,
    }

    return render_to_response(template, RequestContext(request, context_dict))
