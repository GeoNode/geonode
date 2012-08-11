# -*- coding: utf-8 -*-
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

import os
from ConfigParser import SafeConfigParser
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from lxml import etree
from pycsw import server

@csrf_exempt
def csw_global_dispatch(request):

    app_root = os.path.dirname(__file__)

    # serialize settings.CSW into SafeConfigParser
    # object for interaction with pycsw
    config = SafeConfigParser()
    for section, options in settings.CATALOGUE.iteritems():
        config.add_section(section)
        for k, v in options.iteritems():
            config.set(section, k, v)

    scheme = "http"
    if request.is_secure():
        scheme = "https"

    # update server.url
    server_url = '%s://%s/catalogue/csw/' %(scheme, request.META['HTTP_HOST'])
    config.set('server', 'url', server_url)

    # request.meta has:
    # QUERY_STRING, REMOTE_ADDR, CONTENT_LENGTH, SERVER_NAME
    # SERVER_PORT
    env = request.META.copy()
    env.update({
            'local.app_root': app_root,
            'REQUEST_URI': request.build_absolute_uri(),
            'REQUEST_METHOD': request.method,
            'wsgi.url_scheme': scheme,
            'PATH_INFO': request.path_info,
            'wsgi.input': request # this is being a bit sneaky but w/e
            })
            
    csw = server.Csw(config, env)

    content = csw.dispatch_wsgi()

    return HttpResponse(content, content_type=csw.contenttype)

def csw_local_dispatch(request):
    """
    HTTP-less CSW
    """
    # set up configuration
    config = SafeConfigParser()

    for section, options in settings.CATALOGUE.iteritems():
        config.add_section(section)
        for option, value in options.iteritems():
            config.set(section, option, value)

    # fake HTTP environment variable
    os.environ['QUERY_STRING'] = ''

    # init pycsw
    csw = server.Csw(config)

    # fake HTTP method
    csw.requesttype = request.method.upper()

    # fake HTTP request parameters
    csw.kvp = {
        'elementsetname': 'brief',
        'typenames': 'csw:Record',
        'resulttype': 'results',
        'constraintlanguage': 'CQL_TEXT',
        #'constraint': 'csw:AnyText like "%iLor%"',
        'constraint': None,
        'maxrecords': '2'
    }

    response = csw.getrecords()
    response_string = etree.tostring(response)

    return HttpResponse(response, content_type=csw.contenttype)
