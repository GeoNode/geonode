#!/bin/sh

# Exit script in case of error
set -e

if [ ! -z "${S3_ACCESS_KEY}" ]; then
    rclone sync -v --config /rclone.s3.conf /spcgeonode-geodatadir/ spcgeonode:geodatadir/
    rclone sync -v --config /rclone.s3.conf /spcgeonode-media/ spcgeonode:media/
    rclone sync -v --config /rclone.s3.conf /spcgeonode-pgdumps/ spcgeonode:pgdumps/

    echo "S3 sync successful !!"
fi

echo "Finished syncing"
