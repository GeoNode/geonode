start_debug:
	echo 'Start geonode on ip 0.0.0.0:8000'
	paver start -b 0.0.0.0:8000

start_django_debug:
	echo 'Start geonode on ip 0.0.0.0:8000'
	paver start_django -b 0.0.0.0:8000
