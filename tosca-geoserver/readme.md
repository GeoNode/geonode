docker tag tosca-geonode-nginx:dev orttak/tosca-geonode-nginx:latest
docker push orttak/tosca-geonode-nginx:latest

docker tag tosca-geonode-geoserver:2.24.4 orttak/tosca-geonode-geoserver:2.24.4
docker push orttak/tosca-geonode-geoserver:2.24.4

docker tag geoserver-2.24.4-tosca-data:latest orttak/geoserver-2.24.4-tosca-data:latest
docker push orttak/geoserver-2.24.4-tosca-data:latest

