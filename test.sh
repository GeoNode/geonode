#!/bin/bash

set -euo pipefail

grant_superuser() {
    local url="${1#*://}"
    local user="${url%%:*}"
    local host="${url#*@}"; host="${host%%:*}"
    local port="${url#*:}"; port="${port#*:}"; port="${port%%/*}"

    echo "Granting SUPERUSER to ${user} (${host}:${port})..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${host}" -p "${port}" -U postgres \
        -c "ALTER ROLE ${user} SUPERUSER;"
}

grant_superuser "${DATABASE_URL}"
grant_superuser "${GEODATABASE_URL}"

echo "PG setup done."
echo "Start loading data."

GISDATA_DIR=$(python -c "import gisdata; print(gisdata.GOOD_DATA)")

TYPE="${1:-}"
DATA_DIR="${GISDATA_DIR}"
if [[ "${TYPE}" =~ ^(vector|raster|time)$ ]]; then
    DATA_DIR="${GISDATA_DIR}/${TYPE}"
fi

if [[ ! -d "${MEDIA_ROOT}" ]]; then
    echo "media root not available, creating..."
    mkdir -p "${MEDIA_ROOT}"
fi

python -W ignore manage.py importlayers -v2 -hh "${SITEURL}" "${DATA_DIR}"

echo "Loading data done."
echo "Start test"
coverage run --branch --source=geonode manage.py test -v 3 --keepdb $@
echo "test completed."