up:
	# bring up the services
	docker-compose up -d

build:
	docker pull python:2.7
	docker build -t geonode/django:latest .
	docker build -t geonode/django:`date +%Y%m%d%H%M%S` .

migrate:
	django-admin.py migrate --noinput

migrate_setup: migrate
	django-admin.py loaddata sample_admin

wait:
	sleep 5

logs:
	docker-compose logs --follow

down:
	docker-compose down

pull:
	docker-compose pull

smoketest: up
	docker-compose exec django python manage.py test geonode.tests.smoke --noinput --nocapture --detailed-errors --verbosity=1 --failfast

unittest: up
	docker-compose exec django python manage.py test geonode.people.tests geonode.base.tests geonode.layers.tests geonode.maps.tests geonode.proxy.tests geonode.security.tests geonode.social.tests geonode.catalogue.tests geonode.documents.tests geonode.api.tests geonode.groups.tests geonode.services.tests geonode.geoserver.tests geonode.upload.tests geonode.tasks.tests --noinput --failfast

test: smoketest unittest

clear:
	docker-compose down --volumes

hardreset: pull build reset

develop: pull build up sync
