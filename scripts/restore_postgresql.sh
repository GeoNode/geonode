# run this script as the postgres user
bk_dir=/data/backups/postgres
cd $bk_dir
bk_date=20170416

# restore main backups
for db_name in worldmaplegacy wmdata geonetwork dataverse; do
    psql -c "DROP DATABASE $db_name;"
    psql -c "CREATE DATABASE $db_name WITH OWNER worldmap;"
    bk_name="$bk_date.$db_name.sql.gz"
    echo "Restoring $db_name..."
    gunzip < $bk_name | psql $db_name
done

# restore shards backup
for year in $(seq 2016 2020); do
    for month in 01 02 03 04 05 06 07 08 09 10 11 12; do
        db_name="wm_$year$month"
        bk_name="$bk_date.$db_name.sql.gz"
        psql -c "DROP DATABASE $db_name;"
        psql -c "CREATE DATABASE $db_name WITH OWNER worldmap;"
        psql -c "CREATE EXTENSION postgis;" $db_name
        echo "Restoring $db_name..."
        gunzip < $bk_name | psql $db_name
    done
done
