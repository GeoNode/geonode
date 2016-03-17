from django.views.generic import DetailView

from .models import Collection


class CollectionDetail(DetailView):

    model = Collection
