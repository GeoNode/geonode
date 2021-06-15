set -a
. ./.env_dev
set +a

paver $@
