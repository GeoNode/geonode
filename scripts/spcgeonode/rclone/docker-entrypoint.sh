#!/bin/sh

# Exit script in case of error
set -e

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING RCLONE ENTRYPOINT --------------------------"
date

############################
# 1. Assert there is data to be backed up
############################

echo "-----------------------------------------------------"
echo "1. Assert there is data to be backed up"

if [ "$(ls -A /spcgeonode-geodatadir)" ] || [ "$(ls -A /spcgeonode-media)" ] || [ "$(ls -A /spcgeonode-pgdumps)" ]; then
    echo 'Found data do backup'
else
    # If all backups directories are empty, we quit, because
    # we want to make sure backup works by running at least
    # once instead of letting the user believe everything works fine
    echo 'Nothing to backup, we quit...'
    exit 1
fi

############################
# 2. Replacing environment variables
############################

echo "-----------------------------------------------------"
echo "2. Replacing environment variables"
envsubst ' \$S3_ACCESS_KEY \$S3_SECRET_KEY \$S3_REGION \$S3_BUCKET' < /rclone.s3.conf.envsubst > /rclone.s3.conf
# TODO : remove this
cat /rclone.s3.conf

############################
# 3. Running once to ensure config works
############################

echo "-----------------------------------------------------"
echo "3. Running once to ensure config works"
/root/sync.sh

echo "-----------------------------------------------------"
echo "FINISHED RCLONE ENTRYPOINT --------------------------"
echo "-----------------------------------------------------"

# Run the CMD 
exec "$@"
