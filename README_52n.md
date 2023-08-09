# 52°North Fork of GeoNode

This image is built from a fork of [Geonode](https://github.com/geonode/geonode).
[52°North GmbH](https://52north.org) maintains an own fork of GeoNode in order to make necessary adjustments within projects which are not part of GeoNode core.

However, we are interested to stay as close to upstream as possible, to benefit from ongoing development, but also to contribute features and fixes we develop in our projects.

Starting from version `4` this image is built from the `52n-master` branch of the [`52north/geonode` repository](https://github.com/52North/geonode/tree/52n-master).
The repository builds and publishes three images:

* [`52north/geonode`](https://hub.docker.com/r/52north/geonode) (this image)
* [`52north/geonode-nginx`](https://hub.docker.com/r/52north/geonode-nginx)
* [`52north/geonode-geoserver`](https://hub.docker.com/r/52north/geonode-geoserver) 

The Dockerfiles can be found under the [`./scripts/docker` folder](https://github.com/52North/geonode/tree/52n-master/scripts/docker).

The official Docker configuration of [GeoServer for GeoNode](https://github.com/GeoNode/geoserver-docker) seems to be outdated.
Therefore, our fork adds a `./scripts/docker/geoserver` Docker config which is based on [the geonode-project](https://github.com/geonode/geonode-project) template.

Depending on our current project contexts we merge regularly from upstream, and create new pull requests based on this fork.

> **Note on version `3` tags**
>
> Images containing a `3.x` version tag were experimental and do have a different code base.
> These image are considered to be removed in the near future.