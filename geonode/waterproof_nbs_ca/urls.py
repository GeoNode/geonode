"""URLs for the ``WaterProof NBS CA`` module."""
from django.conf.urls import url, include

from . import views


urlpatterns = [
    url(r'^$',
        views.WaterproofNbsCaListView.as_view(),
        name='waterproof_nbs_ca_list'),

    url(r'^create/$',
        views.WaterproofNbsCaCreateView.as_view(),
        name='waterproof_nbs_ca_submit'),

    url(r'^sbn/(?P<pk>\d+)/update/$', views.WaterproofNbsUpdateView.as_view(), name='waterproof_update'),

    url(r'^sbn/(?P<pk>\d+)/detail/$', views.WaterproofNbsCaDetailView.as_view(), name='waterproof_detail'),

    url(r'^sbn/(?P<pk>\d+)/delete/$', views.WaterproofNbsDeleteView.as_view(), name='waterproof_delete'),


]
