from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.shortcuts import render, render_to_response, redirect
from django.utils import simplejson as json

from pprint import pprint

import traceback
import urllib2

@login_required
def geocode(request, resp_format="json"):
    if request.method == 'GET':
        raise HttpResponseForbidden
    status_code = 400
    address=None
    pprint(request.POST)
    if 'geocode_input' in request.POST:
        address = request.POST['geocode_input']
    args={
        'address':  urllib2.unquote_plus(address),
        'key': GEOCODE_API_KEY
    }
    try:
        data = urllib2.urlencode(args)
        response = urllib2.urlopen(geocode_url+resp_format+"?", data)
        resp_data = json.loads(response.read())
        status_code = response.getcode()
        pprint(resp_data)
    except Exception as e:
        resp_data = ''
        print traceback.format_exc()
    
    return HttpResponse(
            json.dumps(resp_data),
            mimetype='application/json',
            status=status_code)
