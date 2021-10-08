set -a
. ./.env_dev
set +a

celery -A geonode.celery_app:app worker --without-gossip --without-mingle -Ofair -B -E --statedb=worker.state --scheduler=celery.beat:PersistentScheduler --loglevel=DEBUG --concurrency=2 -n worker1@%h
