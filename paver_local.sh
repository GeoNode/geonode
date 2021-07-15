set -a
. ./.env_local
set +a

paver $@
