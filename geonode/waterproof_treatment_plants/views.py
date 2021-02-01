from django.http import HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import render
from geonode.waterproof_nbs_ca.models import Countries, Region, Currency
from geonode.waterproof_intake.models import City, Intake
from rest_framework.decorators import api_view
from django.conf import settings
import requests
import socket


countryPlant = ""
region = ""
currency = ""
city = ""

def loadGlobalVariable(request):
	if request.method == 'GET':
		global countryPlant
		global region
		global currency
		global city
		countryPlant = Countries.objects.get(code=request.user.country)
		region = Region.objects.get(id=countryPlant.region_id)
		currency = Currency.objects.get(id=countryPlant.id)
		city = City.objects.get(id=1)

def treatmentPlantsList(request):
	if request.method == 'GET':
		global countryPlant
		global region
		global currency
		global city

		loadGlobalVariable(request)
		response = requests.get(settings.SITE_HOST_API + 'treatment_plants/rest/')
		return render(
			request,
			'waterproof_treatment_plants/treatment_plants_list.html',
			{
				'city': city,
				'countryPlant': countryPlant,
				'region': region,
				'currency': currency,
				'treatmentPlantsList': response.json()
			}
		)

def editTreatmentPlants(request):
	if request.method == 'GET':
		global countryPlant
		global region
		global currency
		global city
		countryPlant = Countries.objects.get(code=request.user.country)
		region = Region.objects.get(id=countryPlant.region_id)
		currency = Currency.objects.get(id=countryPlant.id)
		city = City.objects.get(id=1)


def newTreatmentPlants(request, userCountryId):
	if request.method == 'GET':
		global countryPlant
		global region
		global currency
		global city

		loadGlobalVariable(request)
		return render(
			request,
			'waterproof_treatment_plants/treatment_plans_edit.html',
			{
				'city': city,
				'countryPlant': countryPlant,
				'region': region,
				'currency': currency,
			}
		)

@api_view(['GET'])
def getTreatmentPlantsList(request):
	if request.method == 'GET':
		jsonObject = [
					{	
						'name' : 'treatment plant test one',
						'description': 'This is the first test, in the list',
						'catchment': 'there is no evidence'
					},
					{	
						'name' : 'treatment plant test two',
						'description': 'This is the second test, in the list',
						'catchment': 'there is no evidence'
					},
					{	
						'name' : 'treatment plant test three',
						'description': 'This is the third test, in the list',
						'catchment': 'there is no evidence'
					}
				]
		return JsonResponse(jsonObject, safe=False)

