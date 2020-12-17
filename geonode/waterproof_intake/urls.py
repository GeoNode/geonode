"""URLs for the ``WaterProof Intake`` module."""
from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
    # Create Water Intake
    path('create/', views.create, name='create'),

]
