#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import json
import urllib

from owslib.wfs import WebFeatureService

log = logging.getLogger(__name__)


class GeoserverDataSource(object):
    """
    Wrapper around WFS to get deserialized features for risk management app
    """
    OUTPUT_FORMATS = {'application/json': json.load}
    WFCLASS = staticmethod(WebFeatureService)

    def __init__(self, url, output_format='application/json', **kwargs):
        self.wfs = GeoserverDataSource.WFCLASS(url=url, version='2.0.0', **kwargs)
        self.output_format = output_format

    def prepare_vparams(self, vparams, separator=":"):
        u = urllib.quote
        return [separator.join((u(k), u(str(v)),)) for k, v in vparams.iteritems()]

    def prepare_cql_params(self, vparams, separator="="):
        u = urllib.quote
        return [separator.join((u(k), "'{}'".format(v),)) for k, v in vparams.iteritems()]

    def get_features(self, layer_name, dim_name=None, **kwargs):
        """
        Return deserialized featurelist for given params
        @param kwargs keyword args used in viewparams
        @param dim_name optional dimension to be not null
        """
        # kwargs['dim'] = dim_name
        # vparams_list = self.prepare_vparams(kwargs)
        # vparams = {'viewparams': ';'.join(vparams_list)}
        # field_names = ['dim1', 'dim2', 'value']
        # r = self.wfs.getfeature(layer_name, propertyname=field_names, outputFormat=self.output_format, storedQueryParams=vparams, storedQueryID=1)

        """
        Using 'viewparams'
        """
        # vparams = {'viewparams': 'ra:WP6_future_proj_Hospital;ha:EQ;region:Afghanistan;adm_code:AF;d1:Hospital;d2:10'}
        # field_names = ['risk_analysis','hazard_type','admin','adm_code','region','value','dim1_value','dim2_value','dim3_value','dim4_value','dim5_value', 'value']
        # r = self.wfs.getfeature('{}'.format(layer_name), propertyname=field_names, outputFormat=self.output_format, storedQueryParams=vparams, storedQueryID=1)

        """
        Using 'cql_filter'
        """
        cql_params_list = self.prepare_cql_params(kwargs)
        if dim_name is not None:
            cql_params_list.append('{}_value is not null'.format(dim_name))
        cql_filter = {'cql_filter': " and ".join(cql_params_list)}
        # cql_filter = {'cql_filter': "(risk_analysis='WP6_future_proj_Hospital' and hazard_type='EQ' and adm_code='AF' and dim1_value='Hospital')"}
        field_names = ['risk_analysis', 'hazard_type', 'admin', 'adm_code', 'region',
                       'dim1_value', 'dim2_value', 'dim3_value', 'dim4_value', 'dim5_value',
                       'dim1_order', 'dim2_order', 'dim3_order', 'dim4_order', 'dim5_order',
                       'value']
        log.info("querying %s:%s with cql params: %s", layer_name, dim_name, cql_filter)
        # r = self.wfs.getfeature('{}_data'.format(layer_name), propertyname=field_names, outputFormat=self.output_format, storedQueryParams=cql_filter, storedQueryID=1)
        r = self.wfs.getfeature('{}_data'.format(layer_name), propertyname=field_names, outputFormat=self.output_format, storedQueryParams=cql_filter, storedQueryID='risk_data_cql')

        return self.deserialize(r)

    def deserialize(self, val):
        d = self.OUTPUT_FORMATS[self.output_format]
        return d(val)
