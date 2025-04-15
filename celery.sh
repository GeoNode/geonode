#!/bin/bash
nohup celery -A geonode.celery_app:app beat -l DEBUG -f /var/log/celery.log &>/dev/null &
nohup celery -A geonode.celery_app:app worker --without-gossip --without-mingle -Ofair -B -E --statedb=worker.state --scheduler=celery.beat:PersistentScheduler --loglevel=INFO --concurrency=2 -n worker1@%h -f /var/log/celery.log &>/dev/null