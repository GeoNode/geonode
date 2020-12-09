"""URLs for the ``WaterProof NBS CA`` module."""
from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
    # Create NBS
    path('create/', views.createNbs, name='create-nbs'),
    # Default view, list all views
    path('', views.listNbs, name='list-nbs'),
    # Load all RIOS transitions
    path('load-transitions/', views.loadAllTransitions, name='waterproof_load_transformations'),
    # Load activities by it's transition id
    path('load-activityByTransition/', views.loadActivityByTransition, name='waterproof_load_activities'),
    # Load transformations by it's activity id 
    path('load-transformationByActivity/', views.loadTransformationbyActivity, name='waterproof_load_transformations'),
    # Load a country by id
    path('load-country/', views.loadCountry, name='waterproof_load_country'),
    # Load currency by id
    path('load-currency/', views.loadCurrency, name='waterproof_load_currency')
]
