from django.urls import path
from . import views

urlpatterns = [
      path('', views.treatmentPlantsList, name='treatment-plants-list'),
      path('rest/', views.getTreatmentPlantsList, name='treatment-plants'),
      path('edit/<int:idx>', views.editTreatmentPlants, name='edit-treatment-plants'),
      path('create/<int:userCountryId>', views.newTreatmentPlants, name='create-treatment-plants'),
]