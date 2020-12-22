"""URLs for the ``WaterProof NBS CA`` module."""
from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
    # Create NBS
    path('create/<int:countryId>', views.createNbs, name='create-nbs'),
    # Default view, list all views
    path('', views.listNbs, name='list-nbs'),
    # View NBS details
    path('view/<int:idx>', views.viewNbs, name='view-nbs'),
    # Edit NBS
    path('edit/<int:idx>', views.editNbs, name='edit-nbs'),
    # Clone NBS
    path('clone/<int:idx>', views.cloneNbs, name='clone-nbs'),
    # Delete NBS
    path('delete/<int:idx>', views.deleteNbs, name='delete-nbs'),
    # Load all RIOS transitions
    path('load-transitions/', views.loadAllTransitions, name='waterproof_load_transformations'),
    # Load activities by it's transition id
    path('load-activityByTransition/', views.loadActivityByTransition, name='waterproof_load_activities'),
    # Load transformations by it's activity id
    path('load-transformationByActivity/', views.loadTransformationbyActivity, name='waterproof_load_transformations'),
    # Load a country by id
    path('load-country/', views.loadCountry, name='waterproof_load_country'),
    # Load a country by id
    path('load-countryByCode/', views.loadCountryByCode, name='waterproof_load_countryByCode'),
    # Load all countries
    path('load-allCountries/', views.loadAllCountries, name='load_allCountries'),
    # Load currency by id
    path('load-currency/', views.loadCurrency, name='load_currency'),
    # Load currency by country id
    path('load-currencyByCountry/', views.loadCurrencyByCountry, name='load_currencyByCountry'),
     # Load region by country id
    path('load-regionByCountry/', views.loadRegionByCountry, name='load_regionByCountry'),
    # Load all currencies
    path('load-allCurrencies/', views.loadAllCurrencies, name='load_allCurrencies')
]
