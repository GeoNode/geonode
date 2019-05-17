#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import logging

from django.conf import settings
from django.views.generic import TemplateView, View
from django.contrib.gis.gdal import OGRGeometry

from geonode.utils import json_response
from geonode.contrib.risks.models import (HazardType, AdministrativeDivision,
                                          RiskAnalysisDymensionInfoAssociation)
from geonode.contrib.risks.views import AppAware

from geonode.contrib.risks.datasource import GeoserverDataSource

log = logging.getLogger(__name__)


class AdministrativeGeometry(AppAware, View):
    

    def _get_geometry(self, val):
        """
        converts geometry to geojson geom
        """
        g = OGRGeometry(val)
        return json.loads(g.json)

    def _get_properties(self, val):
        return val.export()

    def _make_feature(self, val, app):
        """
        Returns feature from the object

        """
        return {"type": "Feature",
                "properties": self._get_properties(val.set_app(app)),
                "geometry": self._get_geometry(val.geom)
                }


    def get(self, request, adm_code, **kwargs):
        try:
            app = self.get_app()
        except KeyError:
            app = None
        try:
            adm = AdministrativeDivision.objects.get(code=adm_code)
        except AdministrativeDivision.DoesNotExist:
            adm = None
        if adm is None:
            return json_response(errors=["Invalid code"], status=404)

        children = adm.children.all()
        _features = [adm] + list(children)

        features = [self._make_feature(item, app) for item in _features]
        out = {'type': 'FeatureCollection',
               'features': features}
        return json_response(out)
                           

administrative_division_view = AdministrativeGeometry.as_view()
