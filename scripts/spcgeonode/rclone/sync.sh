#!/bin/sh

# Exit script in case of error
set -e

rclone sync -v --config /run/secrets/rclone_backup_conf /spcgeonode-geodatadir/ spcgeonode:geodatadir/
rclone sync -v --config /run/secrets/rclone_backup_conf /spcgeonode-media/ spcgeonode:media/
rclone sync -v --config /run/secrets/rclone_backup_conf /spcgeonode-pgdumps/ spcgeonode:pgdumps/

echo "-----------------------------------------------------"
echo "Sync successful !!"
