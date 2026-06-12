#!/bin/bash
set -o allexport
source ../.env
set +o allexport
docker compose -f ../docker-compose.yml -f ./docker-compose.yml  "$@"