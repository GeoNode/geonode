dropdb geonode
dropdb geonode_imports
dropuser geonode
createuser geonode -d
createdb -O geonode geonode
createdb -O geonode geonode_imports
psql -d geonode_imports -c "create extension postgis;"
psql -d geonode_imports -c "grant all on geometry_columns to public;"
psql -d geonode_imports -c "grant all on geography_columns to public;"
