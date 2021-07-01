set -a
. ./.env_local
set +a

python manage.py $@
