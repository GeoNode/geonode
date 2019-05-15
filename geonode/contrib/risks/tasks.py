#!/usr/bin/env python
# -*- coding: utf-8 -*-

import StringIO
import traceback

from celery.task import task
from django.conf import settings
from django.core.mail import send_mail
from django.core.management import call_command

from geonode.contrib.risks.models import RiskAnalysis, HazardSet

def create_risk_analysis(input_file, file_ini):
    _create_risk_analysis.apply_async(args=(input_file, file_ini))


@task(name='geonode.contrib.risks.tasks.create_risk_analysis')
def _create_risk_analysis(input_file, file_ini):
    out = StringIO.StringIO()
    risk = None
    try:
        call_command('createriskanalysis',
                     descriptor_file=str(input_file).strip(), stdout=out)
        value = out.getvalue()

        risk = RiskAnalysis.objects.get(name=str(value).strip())
        risk.descriptor_file = file_ini
        risk.save()
    except Exception, e:
        value = None
        if risk is not None:
            risk.set_error()
        error_message = "Sorry, the input file is not valid: {}".format(e)
        raise ValueError(error_message)


def import_risk_data(input_file, risk_app, risk_analysis, region, final_name):
    risk_analysis.set_queued()
    _import_risk_data.apply_async(args=(input_file, risk_app.name, risk_analysis.name, region.name, final_name,))

@task(name='geonode.contrib.risks.tasks.import_risk_data')
def _import_risk_data(input_file, risk_app_name, risk_analysis_name, region_name, final_name):
        out = StringIO.StringIO()
        risk = None
        try:
            risk = RiskAnalysis.objects.get(name=risk_analysis_name)
            risk.set_processing()
            # value = out.getvalue()
            call_command('importriskdata',
                         commit=False,
                         risk_app=risk_app_name,
                         region=region_name,
                         excel_file=input_file,
                         risk_analysis=risk_analysis_name,
                         stdout=out)
            risk.refresh_from_db()
            risk.data_file = final_name
            risk.save()
            risk.set_ready()
        except Exception, e:
            error_message = "Sorry, the input file is not valid: {}".format(e)
            if risk is not None:
                risk.save()
                risk.set_error()
            raise ValueError(error_message)

def import_risk_metadata(input_file, risk_app, risk_analysis, region, final_name):
    risk_analysis.set_queued()
    _import_risk_metadata.apply_async(args=(input_file, risk_app.name, risk_analysis.name, region.name, final_name,))


@task(name='geonode.contrib.risks.tasks.import_risk_metadata')
def _import_risk_metadata(input_file, risk_app_name, risk_analysis_name, region_name, final_name):
        out = StringIO.StringIO()
        risk = None
        try:
            risk = RiskAnalysis.objects.get(name=risk_analysis_name)
            risk.set_processing()
            call_command('importriskmetadata',
                         commit=False,
                         risk_app=risk_app_name,
                         region=region_name,
                         excel_file=input_file,
                         risk_analysis=risk_analysis_name,
                         stdout=out)
            # value = out.getvalue()
            risk.refresh_from_db()
            risk.metadata_file = final_name
            hazardsets = HazardSet.objects.filter(riskanalysis__name=risk_analysis_name,
                                                  country__name=region_name)
            if len(hazardsets) > 0:
                hazardset = hazardsets[0]
                risk.hazardset = hazardset

            risk.save()
            risk.set_ready()
        except Exception, e:
            error_message = "Sorry, the input file is not valid: {}".format(e)
            if risk is not None:
                risk.set_error()
            raise ValueError(error_message)
