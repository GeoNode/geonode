#!/bin/bash

# Fixes the ownership of the named volumes, so the services can run as non-root users.
# Runs as root in the permissions-init service, before the other services start.
set -euo pipefail

VOLUMES_ROOT=${PERMISSIONS_INIT_VOLUMES_ROOT:-/volumes}
# bump the version when the ownership rules change, so existing volumes are fixed again
MARKER=.geonode-permissions-v1
SKIP=${PERMISSIONS_INIT_SKIP:-}
SKIP=",${SKIP// /},"
case ${PERMISSIONS_INIT_FORCE:-false} in
    [Tt][Rr][Uu][Ee]|[Yy][Ee][Ss]|[Oo][Nn]|1) FORCE=true;;
    *) FORCE=false;;
esac

# name:uid:gid:access, access is shared (group can write) or private (owner only)
VOLUMES=(
    statics:1000:0:shared
    geoserver-data-dir:1000:0:shared
    backup-restore:1000:0:shared
    nginx-confd:101:0:shared
    nginx-certificates:101:0:shared
    dbdata:70:70:private
    dbbackups:70:70:private
)

fix_volume () {
    local _name=$1 _uid=$2 _gid=$3 _access=$4
    local _path="${VOLUMES_ROOT}/${_name}"
    local _start
    _start=$(date +%s%N)

    if [ ! -d "$_path" ]; then
        echo "${_name}: not mounted, skipped"
        return
    fi
    if [[ $SKIP == *",${_name},"* ]]; then
        echo "${_name}: listed in PERMISSIONS_INIT_SKIP, skipped"
        return
    fi
    if [ -e "${_path}/${MARKER}" ] && [ "$FORCE" = "false" ]; then
        echo "${_name}: already fixed, skipped"
        return
    fi

    # an empty volume gets no marker: Docker copies the image content only into an empty volume, and initdb refuses a non-empty one
    local _empty=false
    if [ -z "$(find "$_path" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
        _empty=true
    fi

    # one pass, large volumes are slow to walk; -h and find without -L: symlinks are never followed out of the volume
    if [ "$_access" = "shared" ]; then
        find "$_path" \( ! -user "$_uid" -o ! -group "$_gid" \) -exec chown -h "${_uid}:${_gid}" {} + \
            , -type d ! -perm -2070 -exec chmod g+rwxs {} + \
            , -type f ! -perm -060 -exec chmod g+rw {} +
    else
        find "$_path" \( ! -user "$_uid" -o ! -group "$_gid" \) -exec chown -h "${_uid}:${_gid}" {} +
    fi

    if [ "$_empty" = "false" ]; then
        touch "${_path}/${MARKER}"
    fi
    echo "${_name}: owner ${_uid}:${_gid}, ${_access} access, $(( ($(date +%s%N) - _start) / 1000000 )) ms"
}

for _volume in "${VOLUMES[@]}"; do
    IFS=: read -r _name _uid _gid _access <<< "$_volume"
    fix_volume "$_name" "$_uid" "$_gid" "$_access"
done
