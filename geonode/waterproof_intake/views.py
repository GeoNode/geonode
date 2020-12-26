"""
Views for the ``Waterproof intake`` application.

"""

import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from .models import ExternalInputs
from .models import City
from . import forms
from . import models
from .models import Intake

logger = logging.getLogger(__name__)


def create(request):
    logger.debug(request.method)
    if request.method == 'POST':
        form = forms.IntakeForm(request.POST)
        if form.is_valid():
            intake = form.save(commit=False)
            """
            zf = zipfile.ZipFile(request.FILES['area'])
            print(zf.namelist())
            for filename in zf.namelist():
                if filename=='prevent_grass_strips_slope_gura.shp':
                    print('es el que es')
            """
            intake.save()
            messages.success(request, ("Water Intake created."))
        else:
            messages.error(request, ("Water Intake not created."))

    else:
        form = forms.IntakeForm()
    return render(request, 'waterproof_intake/intake_form.html', context={"form": form, "serverApi": settings.WATERPROOF_API_SERVER})


def listIntake(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            if (request.user.professional_role == 'ADMIN'):

                intake = Intake.objects.all()
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_intake/intake_list.html',
                    {
                        'intake': intake,
                        'city': city,
                    }
                )
        
            if (request.user.professional_role == 'ANAL'):
                intake = Intake.objects.all()
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_intake/intake_list.html',
                    {
                        'intake': intake,
                        'city': city,
                    }
                )
        else:
            intake = Intake.objects.all()
            city = City.objects.all()
            return render(
                request,
                'waterproof_intake/intake_list.html',
                {
                    'intake': intake,
                    'city': city,
                }
            )