"""URLs for the ``WaterProof NBS CA`` module."""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.WaterproofNbsCaListView.as_view(),
        name='waterproof_nbs_ca_list'),

    url(r'^create/$',
        views.WaterproofNbsCaCreateView.as_view(),
        name='waterproof_nbs_ca_submit'),
    
]
