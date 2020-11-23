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

from .forms import WaterproofNbsCaForm
from .models import WaterproofNbsCa

logger = logging.getLogger(__name__)


class WaterproofNbsCaMixin(object):
    """
    Mixin to handle and arrange the entry list.

    """

    def post(self, request, *args, **kwargs):

        return self.get(self, request, *args, **kwargs)


class WaterproofNbsCaListView(AccessMixin, WaterproofNbsCaMixin, ListView):
    """
    Main view to display all WaterproofNbsCa

    """
    model = WaterproofNbsCa
    template_name = "waterproof_nbs_ca/entry_list.html"
    access_mixin_setting_name = 'WATERPROOF_NBS_CA_ALLOW_ANONYMOUS'
    logger.debug(template_name)

    def get_queryset(self):
        self.queryset = super(WaterproofNbsCaListView, self).get_queryset()
        return self.queryset


class WaterproofNbsCaDetailView(AccessMixin, WaterproofNbsCaMixin, DetailView):
    """
    Main view to display one WaterproofNbsCa.

    """
    model = WaterproofNbsCa
    template_name = "waterproof_nbs_ca/waterproofnbsca_detail_list.html"
    access_mixin_setting_name = 'WATERPROOF_NBS_CA_ALLOW_ANONYMOUS'
    logger.debug(template_name)

    def get_queryset(self):
        self.queryset = super(WaterproofNbsCaDetailView, self).get_queryset()
        return self.queryset


class WaterproofNbsCaCreateView(AccessMixin, CreateView):
    """
    WaterProof Nbs CA Create form view.

    """
    model = WaterproofNbsCa
    form_class = WaterproofNbsCaForm
    access_mixin_setting_name = 'WATERPROOF_NBS_CA_ALLOW_ANONYMOUS'

    def form_valid(self, form):
        return super(WaterproofNbsCaCreateView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(WaterproofNbsCaCreateView, self).get_form_kwargs()

        return kwargs

    def get_success_url(self):
        return reverse('waterproof_nbs_ca_list')


class WaterproofNbsUpdateView(AccessMixin, UpdateView):
    model = WaterproofNbsCa
    access_mixin_setting_name = 'WATERPROOF_NBS_CA_ALLOW_ANONYMOUS'
    fields = [
        'name',
        'description',
        'max_benefit_req_time',
        'profit_pct_time_inter_assoc',
        'total_profits_sbn_consec_time',
        'unit_implementation_cost',
        'unit_maintenance_cost',
        'periodicity_maitenance',
        'unit_oportunity_cost',
        'rios_transition',
        'land_cover_def'
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
