"""
Views for the ``Waterproof intake`` application.

"""

import logging

from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _

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
            intake.save()
        else:
            intake = Intake(
                name = "intake 6",
                description = "intake 5",
                id_region = "5",
                id_city = "5",
            )
            intake.save()
        messages.success(request, ("Water Intake created."))        
    else:
        form = forms.IntakeForm()
    return render(request, 'waterproof_intake/intake_form.html', context={"form": form})