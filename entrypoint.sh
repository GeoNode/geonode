#!/bin/bash
set -e

/usr/local/bin/invoke update >> /usr/src/app/invoke.log

/usr/local/bin/invoke migrations >> /usr/src/app/invoke.log
/usr/local/bin/invoke prepare >> /usr/src/app/invoke.log
/usr/local/bin/invoke fixtures >> /usr/src/app/invoke.log

source /root/.override_env

exec "$@"
