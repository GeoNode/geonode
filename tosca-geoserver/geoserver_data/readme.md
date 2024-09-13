# Geoserver Data Directory Image for Tosca APP

docker build . - t geoserver-data-2.24.4:latest
docker tag geoserver-data-2.24.4:latest orttak/geoserver-data-2.24.4:latest
docker push orttak/geoserver-data-2.24.4:latest

For Tosca app we create new docker image according to geonode documentation.
- gwc endpoint give error for anonymus request. We just delete and apply same settings
- add vector and raster worksapce and we define vector is default workspace
- Mbtiles defautl tiling setting for vector for raster png is default settings