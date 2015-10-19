from django.shortcuts import render
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView

from geosafe.models import Metadata
from geosafe.forms.metadata import MetadataUploadForm

# Create your views here.

class MetadataListView(ListView):
    model = Metadata
    template_name = 'geosafe/metadata_list.html'

    def get_context_data(self, **kwargs):
        context = super(MetadataListView, self).get_context_data(**kwargs)
        return context

class MetadataCreate(CreateView):
    model = Metadata

    form_class = MetadataUploadForm
    template_name = 'geosafe/metadata_form.html'

    def get_success_url(self):
        return reverse('metadata-list')

    def get_form_kwargs(self):
        kwargs = super(MetadataCreate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

