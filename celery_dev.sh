set -a
. ./.env_dev
set +a

celery -A geonode.celery_app:app worker --without-gossip --without-mingle -Ofair -B -E -s django_celery_beat.schedulers:DatabaseScheduler --loglevel=DEBUG --concurrency=2 -n worker1@%h
