from django.urls import path
from . import views

urlpatterns = [
      path('', views.treatmentPlantsList, name='treatment-plants-list'),
      path('rest/', views.getTreatmentPlantsList, name='treatment-plants'),
]