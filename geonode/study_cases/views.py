"""
Views for the ``django-StudyCases`` application.

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


class StudyCasesListView(AccessMixin, StudyCasesMixin, ListView):
    """
    Main view to display all StudyCases

    """
    model = StudyCases
    template_name = "study_cases/entry_list.html"
    access_mixin_setting_name = 'STUDY_CASES_ALLOW_ANONYMOUS'
    logger.debug(template_name)

    def get_queryset(self):
        """
        Customized to get the ordered categories and entries from the Mixin.

        """
        self.queryset = super(StudyCasesListView, self).get_queryset()
        return self.queryset


class StudyCasesView(AccessMixin, StudyCasesMixin, DetailView):
    """
    Main view to display one Study Cases.

    """
    model = StudyCasesForm
    template_name = "study_cases/entry_list.html"
    access_mixin_setting_name = 'STUDY_CASES_ALLOW_ANONYMOUS'
    
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
    access_mixin_setting_name = 'STUDY_CASES_ALLOW_ANONYMOUS'    

    def form_valid(self, form):
        return super(StudyCasesCreateView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(StudyCasesCreateView, self).get_form_kwargs()
        
        return kwargs

    def get_success_url(self):
        return reverse('study_cases_list')
