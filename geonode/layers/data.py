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

"""Utilities for accessing data linked to GeoNode layers
"""

# Standard Modules
import csv
import logging

# Django functionality
from django.conf import settings
from django.http import HttpResponse

# Imports for SOS
if 'geonode.geoserver' in settings.INSTALLED_APPS:
    from geonode.geoserver.ows import sos_swe_data_list, sos_observation_xml

logger = logging.getLogger("geonode.layers.data")


def layer_sos(feature, supplementary_info, time=None, mimetype="text/csv"):
    """Return SOS data in mimetype format for a layer that specifies a valid URL.

    Parameters
    ----------
    feature : string
        the ID of a feature from the WFS; this is used as a link to a
        corresponding "feature_of_interest" in the SOS
    supplementary_info : dictionary
        set of parameters used to specify access to the SOS.  For example:
            {"sos_url": "http://sos.server.com:8080/sos",
             "observedProperties": ["urn:ogc:def:phenomenon:OGC:1.0.30:temperature"],
             "offerings": ["WEATHER"]}
    time : string
        Optional.   Time should conform to ISO format: YYYY-MM-DDTHH:mm:ss+-HH
        Instance is given as one time value. Periods of time (start and end) are
        separated by "/". Example: 2009-06-26T10:00:00+01/2009-06-26T11:00:00+01

    Returns
    ------
    HttpResponse with mimetype data, or None if an error is encountered.
    """
    sos_data = HttpResponse(content="Unable to process request", status=500)
    try:
        sup_info = eval(supplementary_info)
        offerings = sup_info.get('offerings')
        url = sup_info.get('sos_url')
        observedProperties = sup_info.get('observedProperties')
        time = time
        XML = sos_observation_xml(
            url, offerings=offerings, observedProperties=observedProperties,
            allProperties=False, feature=feature, eventTime=time)
        lists = sos_swe_data_list(XML)
        if mimetype == "text/csv":
            sos_data = HttpResponse(mimetype='text/csv')
            sos_data['Content-Disposition'] = 'attachment;filename=sos.csv'
            writer = csv.writer(sos_data)
            # headers are included by default in lists, can set show_headers to
            #   false in the sos_swe_data_list() in ows.py
            writer.writerows(lists)
        elif mimetype == "application/json":
            pass
            # TODO set the response to return JSON including format, data and style info
            # service_result =  { format: ...,
            #                    'data': sos_data,
            #                     style: ...}
            # return HttpResponse(json.dumps(service_result), mimetype="application/json")
        else:
            pass
    except SyntaxError, e:
        logger.exception(e)
    return sos_data


def layer_netcdf(request, supplementary_info, time=None, mimetype="text/csv"):
    """Return netCDF data in CSV format for a layer that specifies a valid URL.

    Parameters
    ----------
    supplementary_info : dictionary
        a set of parameters used to access a netCDF.  For example:
            {"url": "http://netcdf.server.com/",
             "property": ["urn:ogc:def:phenomenon:OGC:1.0.30:temperature"],
             "offerings": ["WEATHER"]}
    time : string
        Optional.   Time should conform to ISO format: YYYY-MM-DDTHH:mm:ss+-HH
        Instance is given as one time value. Periods of time (start and end) are
        separated by "/". Example: 2009-06-26T10:00:00+01/2009-06-26T11:00:00+01

    Returns
    ------
    HttpResponse with mimetype data, or None if an error is encountered.
    """
    #TODO
    netcdf_data = HttpResponse(content="Unable to process request", status=500)
    return netcdf_data