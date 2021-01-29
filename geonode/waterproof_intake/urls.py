"""URLs for the ``WaterProof Intake`` module."""
from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
    # Create Water Intake
    path('create/', views.create, name='create'),
    # Default view, list all views
    path('', views.listIntake, name='list-intake'),
    # Edit Water Intake
    path('edit/<int:idx>', views.editIntake, name='edit-intake'),
    # View intake detail
    path('view/<int:idx>', views.viewIntake, name='view-intake'),
    # Clone Water Intake
    path('clone/<int:idx>', views.cloneIntake, name='clone-intake'),
    # Clone Water Intake
    path('delete/<int:idx>', views.deleteIntake, name='delete-intake'),
    # Load process effciciency by ID
    path('loadProcess/<str:category>', views.loadProcessEfficiency, name='load-process'),
    # Load function cost by symbol
    path('loadFunctionBySymbol/<str:symbol>', views.loadCostFunctionsProcess, name='load-functionCost'),
    # Load process effciciency by ID
    path('validateGeometry/', views.validateGeometry, name='valid-geometry'),
]
