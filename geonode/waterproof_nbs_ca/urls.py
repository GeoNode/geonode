"""URLs for the ``WaterProof NBS CA`` module."""
from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.createNbs, name='create-nbs'),
    path('list/', views.listNbs, name='list-nbs')
]
