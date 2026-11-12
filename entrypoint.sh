#!/bin/bash

# Exit script in case of error
set -e

# services share group 0, new files must stay writable by the group
umask 0002

parse_bool () {
    case $1 in
        [Tt][Rr][Uu][Ee]|[Yy][Ee][Ss]|[Oo][Nn]|1) echo 'true';;
        *) echo 'false';;
    esac
}

INVOKE_LOG_STDOUT=${INVOKE_LOG_STDOUT:-false}
invoke () {
    if [ $(parse_bool $INVOKE_LOG_STDOUT) = 'true' ]
    then
        $(which invoke) $@
    else
        $(which invoke) $@ > /var/log/geonode/invoke.log 2>&1
    fi
    echo "$@ tasks done"
}

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING DJANGO ENTRYPOINT $(date)"
echo "-----------------------------------------------------"

# an arbitrary UID may have no passwd entry and no writable home
if [ ! -w "$HOME" ] || [ "$HOME" = "/" ]; then
    echo "No usable home for UID $(id -u), using /tmp as HOME"
    export HOME=/tmp
fi

STATIC_ROOT="${STATIC_ROOT:-/mnt/volumes/statics/static/}"
for _dir in "$(dirname "$STATIC_ROOT")" /var/log/geonode; do
    if [ ! -w "$_dir" ]; then
        echo "ERROR: UID $(id -u) cannot write to ${_dir}, fix the volumes ownership with:"
        echo "    docker compose run --rm -e PERMISSIONS_INIT_FORCE=true permissions-init"
        exit 1
    fi
done

invoke update

if [ ! -e $HOME/.bashrc ]; then
    cp /etc/skel/.bashrc $HOME/.bashrc
fi
source $HOME/.bashrc

if [ -e $HOME/.override_env ]; then
    source $HOME/.override_env
fi

cmd="$@"

if [ $(parse_bool $IS_CELERY) = 'true' ]
then
    echo "Executing Celery server $cmd for Production"
else

    invoke migrations
    invoke prepare

    LOCKFILE_DIR="$(dirname "$STATIC_ROOT")"
    if [ $(parse_bool $FORCE_REINIT) = 'true' ] || [ ! -e "${LOCKFILE_DIR}/geonode_init.lock" ]; then
        invoke fixtures
        invoke initialized
        invoke updateadmin
    fi

    invoke statics
    invoke loadthesauri

    echo "Executing UWSGI server $cmd for Production"
fi

echo "-----------------------------------------------------"
echo "FINISHED DJANGO ENTRYPOINT --------------------------"
echo "-----------------------------------------------------"

# Run the CMD
echo "got command $cmd"
exec $cmd
