from django.core.urlresolvers import reverse
from django.views.generic import (
    DetailView, ListView, CreateView, UpdateView, DeleteView)

from geosafe.models import Metadata, Analysis
from geosafe.forms import (AnalysisCreationForm)


class AnalysisCreateView(CreateView):
    model = Analysis
    form_class = AnalysisCreationForm
    template_name = 'geosafe/analysis/create.html'
    context_object_name = 'analysis'

    def get_success_url(self):
        return reverse('metadata-list')

    def get_form_kwargs(self):
        kwargs = super(AnalysisCreateView, self).get_form_kwargs()
        # kwargs.update({'user': self.request.user})
        return kwargs