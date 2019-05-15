#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from geonode.contrib.risks import views
from geonode.contrib.risks import geometry_views
from geonode.contrib.risks.models import RiskApp

KWARGS_DATA_EXTRACTION = {'app': RiskApp.APP_DATA_EXTRACTION}
KWARGS_COST_BENEFIT_ANALYSIS = {'app': RiskApp.APP_COST_BENEFIT}



geometry_urls = [
    url(r'loc/(?P<adm_code>[\w\-]+)/$', geometry_views.administrative_division_view, name='location'),
]
api_urls = [
    url(r'risk/(?P<risk_id>[\d]+)/layers/$', views.risk_layers, name='layers'),
]

urlpatterns = [
    url(r'^geom/', include(geometry_urls, namespace="geom")),
    url(r'^api/', include(api_urls, namespace='api')),
]

_urls = (
    (r'^$', views.risk_data_extraction_index, 'index',),
    (r'^geom/(?P<adm_code>[\w\-]+)/$', geometry_views.administrative_division_view, 'geometry',),
    (r'loc/(?P<loc>[\w\-]+)/$', views.location_view, 'location',),
    (r'loc/(?P<loc>[\w\-]+)/ht/(?P<ht>[\w\-]+)/$', views.hazard_type_view, 'hazard_type',),
    (r'loc/(?P<loc>[\w\-]+)/ht/(?P<ht>[\w\-]+)/at/(?P<at>[\w\-]+)/$', views.hazard_type_view, 'analysis_type',),
    (r'loc/(?P<loc>[\w\-]+)/ht/(?P<ht>[\w\-]+)/at/(?P<at>[\w\-]+)/an/(?P<an>[\w\-]+)/$', views.data_extraction, 'analysis',),
    (r'loc/(?P<loc>[\w\-]+)/ht/(?P<ht>[\w\-]+)/at/(?P<at>[\w\-]+)/an/(?P<an>[\w\-]+)/dym/(?P<dym>[\w\-]+)$', views.data_extraction, 'analysis_dym',),
    (r'loc/(?P<loc>[\w\-]+)/ht/(?P<ht>[\w\-]+)/at/(?P<at>[\w\-]+)/an/(?P<an>[\w\-]+)/pdf/$', views.pdf_report, 'pdf_report',),
    (r'loc/(?P<loc>[\w\-]+)/ht/(?P<ht>[\w\-]+)/at/(?P<at>[\w\-]+)/an/(?P<an>[\w\-]+)/pdf/(?P<pdf_part>({}))/$'\
        .format('|'.join(views.PDFReportView.PDF_PARTS)), views.pdf_report, 'pdf_report_part',),)

urls_sets = ((RiskApp.APP_DATA_EXTRACTION, KWARGS_DATA_EXTRACTION,),
             (RiskApp.APP_COST_BENEFIT, KWARGS_COST_BENEFIT_ANALYSIS,))


for app_name, kwargs in urls_sets:
    urllist = []
    for r in _urls:
        uname = r[-1]
        r = r[:-1]
        u = url(*r, name=uname, kwargs=kwargs)
        urllist.append(u)
    new_urls = url(r'^{}/'.format(app_name), include(urllist, namespace=app_name))
    urlpatterns.append(new_urls)

