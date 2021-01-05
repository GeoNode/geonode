"""URLs for the ``WaterProof Intake`` module."""
from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
    # Create Water Intake
    path('create/', views.create, name='create'),
    # Default view, list all views
    path('', views.listIntake, name='list-intake'),
    # Load process effciciency by ID
    path('loadProcess/<str:category>', views.loadProcessEfficiency, name='load-process'),
    # Load process effciciency by ID
    path('validateGeometry/', views.validateGeometry, name='valid-geometry'),
]
