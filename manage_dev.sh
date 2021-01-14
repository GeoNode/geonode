set -a
. ./.env_dev
set +a

python manage.py $@
