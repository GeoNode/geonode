# Docker images for GeoNode services
**This is a WIP. Further details will be provided in this README once the repo has been stabilized.**

This repository collects the configurations for the Docker images used by GeoNode and GeoNode project Docker compose files.
It replaces the configurations defined in the following locations:
- https://github.com/GeoNode/geonode-project/tree/master/docker
- https://github.com/GeoNode/geonode/tree/master/scripts/docker (will be removed except the [GeoNode base image](https://github.com/GeoNode/geonode/tree/master/scripts/docker/base/ubuntu))
- https://github.com/GeoNode/geoserver-docker (will be archived and deprecated)
- https://github.com/GeoNode/data-docker (will be archived and deprecated)
- https://github.com/GeoNode/nginx-docker (will be archived and deprecated)
- https://github.com/GeoNode/postgis-docker (will be archived and deprecated)

The [configurations](https://github.com/GeoNode/geonode-project/tree/master/docker) in the GeoNode Project repository will by default inherit from these base images without further configurations. These configurations can be customized inside projects for any specific need.

## Builds and publishing to Docker Hub

Docker images can be built and published in two ways:

- When a new release is pusblished. Tagging follows the {image}#{tag}, and a new geonode/{image}:{tag} is published.
- Using the manual action workflow

Example:
 - A release is done with the tag `geoserver#2.23.3-v2` -> `geonode/geooserver:2.23.3-v2` is built and published to Docker Hub