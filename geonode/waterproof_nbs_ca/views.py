"""
Views for the ``django-WaterproofNbsCa`` application.

"""

import logging

from math import fsum

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from django_libs.views_mixins import AccessMixin
from django.shortcuts import render
from .forms import WaterproofNbsCaForm
from .models import WaterproofNbsCa
from .models import RiosActivity, RiosTransition
from .models import RiosTransformation, TramsformationShapefile
from .models import Countries
from .models import Currency
from django.contrib.gis.geos import Polygon, MultiPolygon, GEOSGeometry
from django.contrib.gis.gdal import OGRGeometry
from django.core import serializers
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import json
from shapely.geometry import shape, Point, Polygon
logger = logging.getLogger(__name__)


def createNbs(request):
    if request.POST.get('action') == 'create-nbs':
        nameNBS = request.POST.get('nameNBS')
        descNBS = request.POST.get('descNBS')
        countryNBS = request.POST.get('countryNBS')
        currencyCost = request.POST.get('currencyCost')
        maxBenefitTime = request.POST.get('maxBenefitTime')
        benefitTimePorc = request.POST.get('benefitTimePorc')
        totalConsecTime = request.POST.get('totalConsecTime')
        maintenancePeriod = request.POST.get('maintenancePeriod')
        implementCost = request.POST.get('implementCost')
        maintenanceCost = request.POST.get('maintenanceCost')
        oportunityCost = request.POST.get('oportunityCost')
        riosTransformation = request.POST.get('riosTransformation')
        restrictedArea = request.FILES.get('restrictedArea')  # request.FILES used for to get files
        areaJson = json.load(restrictedArea)
        for feature in areaJson['features']:
            geom = GEOSGeometry(str(feature['geometry']))

        country = Countries.objects.get(id=countryNBS)
        currency = Currency.objects.get(id=currencyCost)
        transformation = RiosTransformation.objects.get(id=1)
        nbs = WaterproofNbsCa(
            country=country,
            currency=currency,
            name=nameNBS,
            description=descNBS,
            max_benefit_req_time=maxBenefitTime,
            total_profits_sbn_consec_time=totalConsecTime,
            profit_pct_time_inter_assoc=benefitTimePorc,
            unit_implementation_cost=implementCost,
            unit_maintenance_cost=maintenanceCost,
            periodicity_maitenance=maintenancePeriod,
            unit_oportunity_cost=oportunityCost,
        )
        nbs.save()
        nbs.rios_transformations.add(transformation)

        TramsformationShapefile.objects.create(
            name=nameNBS,
            action=descNBS,
            activity=descNBS,
            polygon=GEOSGeometry(geom)
        )

        return render(request, 'waterproof_nbs_ca/waterproofnbsca_form.html')
    else:
        nbs = WaterproofNbsCa.objects.all()
        return render(request, 'waterproof_nbs_ca/waterproofnbsca_form.html', {'nbs': nbs})


def listNbs(request):
    if request.method == 'GET':
        nbs = WaterproofNbsCa.objects.all()
        return render(request, 'waterproof_nbs_ca/waterproofnbsca_list.html', {'nbs': nbs})

def editNbs(request, idx):
    filterNbs = WaterproofNbsCa.objects.filter(id=idx)
    return render(request, 'waterproof_nbs_ca/waterproofnbsca_edit.html', {'nbs': filterNbs})

def viewNbs(request, idx):
    filterNbs = WaterproofNbsCa.objects.filter(id=idx)
    currencies = Currency.objects.all()
    return render(request, 'waterproof_nbs_ca/waterproofnbsca_detail_list.html', {'nbs': filterNbs, 'currencies': currencies})

def loadCurrency(request):
    currency = request.GET.get('currency')
    currencies = Currency.objects.filter(id=currency)
    currencies_serialized = serializers.serialize('json', currencies)
    return JsonResponse(currencies_serialized, safe=False)


def loadCurrencyByCountry(request):
    country_id = request.GET.get('country')
    currency = Currency.objects.filter(country_id=country_id)
    currencies_serialized = serializers.serialize('json', currency)
    return JsonResponse(currencies_serialized, safe=False)


def loadAllCurrencies(request):
    currencies = Currency.objects.all()
    currencies_serialized = serializers.serialize('json', currencies)
    return JsonResponse(currencies_serialized, safe=False)


def loadCountry(request):
    country = request.GET.get('country')
    countries = Countries.objects.filter(id=country)
    countries_serialized = serializers.serialize('json', countries)
    return JsonResponse(countries_serialized, safe=False)


def loadAllTransitions(request):
    transitions = RiosTransition.objects.all()
    transitions_serialized = serializers.serialize('json', transitions)
    return JsonResponse(transitions_serialized, safe=False)


def loadAllCountries(request):
    countries = Countries.objects.all()
    countries_serialized = serializers.serialize('json', countries)
    return JsonResponse(countries_serialized, safe=False)


def loadActivityByTransition(request):
    transition = request.GET.get('transition')
    activities = RiosActivity.objects.filter(transition_id=transition)
    activities_serialized = serializers.serialize('json', activities)
    return JsonResponse(activities_serialized, safe=False)


def loadTransformationbyActivity(request):
    activity = request.GET.get('activity')
    trasformations = RiosTransformation.objects.filter(activity_id=activity)
    transformations_serialized = serializers.serialize('json', trasformations)
    return JsonResponse(transformations_serialized, safe=False)


"""

class WaterproofNbsCaDetailView(AccessMixin, WaterproofNbsCaMixin, DetailView):

    Main view to display one WaterproofNbsCa.


    model = WaterproofNbsCa
    template_name = "waterproof_nbs_ca/waterproofnbsca_detail_list.html"
    access_mixin_setting_name = 'WATERPROOF_NBS_CA_ALLOW_ANONYMOUS'
    logger.debug(template_name)

    def get_queryset(self):
        self.queryset = super(WaterproofNbsCaDetailView, self).get_queryset()
        return self.queryset

class MyCreateView(View):

    def post(self,request):
        nbs = WaterproofNbsCa.objects.all().order_by('-id')
        return render(request, 'waterproofnbsca_form', {'nbs': nbs})


class WaterproofNbsUpdateView(AccessMixin, UpdateView):
    model = WaterproofNbsCa
    access_mixin_setting_name = 'WATERPROOF_NBS_CA_ALLOW_ANONYMOUS'
    fields = [
        'country',
        'currency',
        'name',
        'description',
        'max_benefit_req_time',
        'profit_pct_time_inter_assoc',
        'total_profits_sbn_consec_time',
        'unit_implementation_cost',
        'unit_maintenance_cost',
        'periodicity_maitenance',
        'unit_oportunity_cost',
        'rios_transformations',
        'added_by'
    ]

    def get_success_url(self):
        return reverse('waterproof_nbs_ca_list')


class WaterproofNbsDeleteView(DeleteView):
    model = WaterproofNbsCa
    form_class = WaterproofNbsCaForm
    access_mixin_setting_name = 'WATERPROOF_NBS_CA_ALLOW_ANONYMOUS'

    def form_valid(self, form):
        return super(WaterproofNbsDeleteView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(WaterproofNbsDeleteView, self).get_form_kwargs()

        return kwargs

    def get_success_url(self):
        return reverse('waterproof_nbs_ca_list')


class WaterProofLoadActivities(ListView):
    model = RiosActivity
    template_name = "waterproof_nbs_ca/waterproofnsbca_activities_list_options.html"

    def get_queryset(self):
        transition = self.request.GET.get('transition')
        self.queryset = RiosActivity.objects.filter(transition_id=transition)
        return self.queryset


class WaterProofLoadTransformations(ListView):
    model = RiosTransformation
    template_name = "waterproof_nbs_ca/waterproofnsbca_transformations_list_options.html"

    def get_queryset(self):
        activity = self.request.GET.get('activity')
        self.queryset = RiosTransformation.objects.filter(transition_id=activity)
        return self.queryset


class WaterProofLoadCountryFactor(View):
    def get(self, request):
        country = self.request.GET.get('country')
        countries = Countries.objects.filter(id=country)
        countries_serialized = serializers.serialize('json', countries)
        return JsonResponse(countries_serialized, safe=False)


class WaterProofLoadCurrency(View):
    def get(self, request):
        currency = self.request.GET.get('currency')
        currencies = Currency.objects.filter(id=currency)
        currencies_serialized = serializers.serialize('json', currencies)
        return JsonResponse(currencies_serialized, safe=False)
"""
