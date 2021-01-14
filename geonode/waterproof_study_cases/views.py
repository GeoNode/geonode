"""
Views for the ``django-StudyCases`` application.

"""

import logging

from math import fsum

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from .models import StudyCases
from geonode.waterproof_nbs_ca.models import Countries, Region
from geonode.waterproof_intake.models import City
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView

from django_libs.views_mixins import AccessMixin

from .forms import StudyCasesForm
from .models import StudyCases

logger = logging.getLogger(__name__)


class StudyCasesMixin(object):
    """
    Mixin to handle and arrange the entry list.

    """

    def post(self, request, *args, **kwargs):

        return self.get(self, request, *args, **kwargs)


def listStudyCases(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            if (request.user.professional_role == 'ADMIN'):
                userCountry = Countries.objects.get(code=request.user.country)
                region = Region.objects.get(id=userCountry.region_id)
                studyCases = StudyCases.objects.all()
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_study_cases/studycases_list.html',
                    {
                        'casesList': studyCases,
                        'city': city,
                        'userCountry': userCountry,
                        'region': region
                    }
                )

            if (request.user.professional_role == 'ANALYS'):
                studyCases = StudyCases.objects.all()
                userCountry = Countries.objects.get(code=request.user.country)
                region = Region.objects.get(id=userCountry.region_id)
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_study_cases/studycases_list.html',
                    {
                        'casesList': studyCases,
                        'city': city,
                        'userCountry': userCountry,
                        'region': region
                    }
                )
        else:
            studyCases = StudyCases.objects.all()
            userCountry = Countries.objects.get(code='COL')
            region = Region.objects.get(id=userCountry.region_id)
            city = City.objects.all()
            return render(
                request,
                'waterproof_study_cases/studycases_list.html',
                {
                    'casesList': studyCases,
                    'city': city,
                }
            )


class StudyCasesView(AccessMixin, StudyCasesMixin, DetailView):
    """
    Main view to display one Study Cases.

    """
    model = StudyCasesForm
    template_name = "waterproof_study_cases/entry_list.html"
    access_mixin_setting_name = 'WATERPROOF_STUDY_CASES_ALLOW_ANONYMOUS'

    def get_object(self, **kwargs):
        obj = super(StudyCasesView, self).get_object(**kwargs)
        obj.save()
        return obj

    def get_context_data(self, **kwargs):
        context = super(StudyCasesView, self).get_context_data(**kwargs)
        return context


class StudyCasesCreateView(AccessMixin, CreateView):
    """
    Study Cases Create form view.

    """
    model = StudyCases
    form_class = StudyCasesForm
    access_mixin_setting_name = 'WATERPROOF_STUDY_CASES_ALLOW_ANONYMOUS'

    def form_valid(self, form):
        return super(StudyCasesCreateView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(StudyCasesCreateView, self).get_form_kwargs()

        return kwargs

    def get_success_url(self):
        return reverse('study_cases_list')
