# 52°North Fork of GeoNode

This image is built from a fork of [Geonode](https://github.com/geonode/geonode).
[52°North GmbH](https://52north.org) maintains an own fork of GeoNode in order to make necessary adjustments within projects which are not part of GeoNode core.

However, we are interested to stay as close to upstream as possible, to benefit from ongoing development, but also to contribute features and fixes we develop in our projects.


Starting from version `4` this image is built from branch `52n-<geonode-branchname>` of the [`52north/geonode` repository](https://github.com/52North/geonode/tree/52n-master).
Please note, that GeoNode depends on other components which are also available as Docker images.
These images, however, are maintained, built and published from a [`52north/geonode-docker` repository](https://github.com/52North/geonode-docker).

> :bulb: **Note:**
>
> Please note that the versioning schema is different from the upstream project.
> All images are released and tagged using the GeoNode version.


You can obtain all images from here:

* [`52north/geonode`](https://hub.docker.com/r/52north/geonode) (this image)
* [`52north/geonode-geoserver`](https://hub.docker.com/r/52north/geonode-geoserver)
* [`52north/geonode-geoserver_data`](https://hub.docker.com/r/52north/geonode-geoserver_data)
* [`52north/geonode-nginx`](https://hub.docker.com/r/52north/geonode-nginx)
* [`52north/geonode-postgis`](https://hub.docker.com/r/52north/geonode-postgis)

The Dockerfiles can be found under the [`./scripts/docker` folder](https://github.com/52North/geonode/tree/52n-master/scripts/docker).

The GeoNode Dockerfile can be found under the [`./scripts/docker` folder](https://github.com/52North/geonode/tree/52n-master/scripts/docker).
The Dockerfiles for the dependent components are available at [the geonode-docker repository](https://github.com/52North/geonode-docker).


Depending on our current project contexts we merge regularly from upstream, and create new pull requests based on this fork.

> **Note on version `3` tags**
>
> Images containing a `3.x` version tag were experimental and do have a different code base.
> These image are considered to be removed in the near future.