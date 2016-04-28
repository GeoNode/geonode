from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.shortcuts import render, render_to_response, redirect
from django.utils import simplejson as json
from pprint import pprint

import traceback
import urllib2
import geocoder

from .forms import GeocodeForm

@login_required
def geocode(request):
    context = {}
    if request.method == 'POST':
        form  = GeocodeForm(request.POST)
        pprint(request.POST)
        if form.is_valid():
            g = geocoder.google(form.cleaned_data['geocode_input'],key=settings.GEOCODE_API_KEY, region="PH",components="country:Philippines")
        
            return HttpResponse(json.dumps(g.geojson), status=200, content_type='application/json')
        
    context['status']=400
    response = HttpResponse(json.dumps(context), content_type='application/json')
    response.status_code = 400
    return response
