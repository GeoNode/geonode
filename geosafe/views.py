from django.shortcuts import render
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView, CreateView

from geosafe.models import Metadata
from geosafe.forms.metadata import MetadataUploadForm


# Create your views here.

class MetadataListView(ListView):
    model = Metadata
    template_name = 'geosafe/metadata_list.html'
    context_object_name = 'metadata_list'

    def get_context_data(self, **kwargs):
        context = super(MetadataListView, self).get_context_data(**kwargs)
        return context


class MetadataCreate(CreateView):
    model = Metadata
    form_class = MetadataUploadForm
    template_name = 'geosafe/metadata_form.html'
    context_object_name = 'metadata'

    def get_success_url(self):
        return reverse('metadata-list')

    def get_form_kwargs(self):
        kwargs = super(MetadataCreate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


class MetadataDetailView(DetailView):
    model = Metadata
    template_name = 'geosafe/metadata_detail.html'
    context_object_name = 'metadata'

    def get_object(self, queryset=None):
        obj = super(MetadataDetailView, self).get_object(queryset)
        return obj
