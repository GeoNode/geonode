#!/bin/bash

source ~/.virtualenvs/geonode/bin/activate

# This is the script directory
# pushd $(dirname $0)

# This is the current directory
pushd $PWD

case $1 in
	"backup-file")
		case $2 in
                        "")
                                echo "Missing 'backup-file <backup-file>' path!"
                                ;;
			*)
				echo "Starting Restore from $2"
				DJANGO_SETTINGS_MODULE=geonode.settings python -W ignore manage.py restore --backup-file=$2
                                # e.g.: source-address=localhost:8000 target-address=example.com
				DJANGO_SETTINGS_MODULE=geonode.settings python -W ignore manage.py migrate_baseurl -f --source-address=source-address --target-address=target-address
				;;
		esac
		;;
	*)
		echo "Missing 'backup-file' parameter!"
		;;
esac

exit 0
