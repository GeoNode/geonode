bk_dir=/data/backups/postgres
cd $bk_dir
rm *
today=$(date +"%Y%m%d")
pg_dump -h localhost -U worldmap geonetwork | gzip > $today.geonetwork.sql.gz
pg_dump -h localhost -U worldmap worldmaplegacy | gzip > $today.worldmaplegacy.sql.gz
pg_dump -h localhost -U worldmap wmdata | gzip > $today.wmdata.sql.gz
pg_dump -h localhost -U worldmap dataverse | gzip > $today.dataverse.sql.gz
#pg_dump -h localhost -U worldmap hypermap | gzip > $today.hypermap.sql.gz
# wmdata and shards backup
for year in $(seq 2016 2020); do
    for month in 01 02 03 04 05 06 07 08 09 10 11 12; do
        db_name="wm_$year$month"
        echo backup $db_name
        pg_dump -h localhost -U worldmap $db_name | gzip > $today.$db_name.sql.gz
    done
done
# remove empty backup
find . -type f -size -10M -exec rm {} +
s3cmd put * s3://wm-postgres-backup
