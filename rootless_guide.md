# Run GeoNode as non-root

Until GeoNode 5.2.0 the services still run as root by default. Follow these steps to switch an installation to non-root users. Redis always runs as its own user (`999:1000`), Let's Encrypt stays root.

**1. Use GeoServer and Nginx images that support non-root users.** Until they are published, build them from a [geonode-docker](https://github.com/GeoNode/geonode-docker) checkout that contains the non-root changes:

```bash
cd geonode-docker
docker build -t geonode/geoserver:rootless docker/geoserver
docker build -t geonode/nginx:rootless docker/nginx
```

Then point GeoNode to them in a `docker-compose.override.yml` next to `docker-compose.yml`:

```yaml
services:
  geoserver:
    image: geonode/geoserver:rootless
  nginx:
    image: geonode/nginx:rootless
```

**2. Rebuild the GeoNode image**, it creates the folders the non-root user writes to:

```bash
docker compose build
```

**3. Set the users in `.env`:**

```bash
GEONODE_UID_GID=1000:0
DB_UID_GID=70:70
GEOSERVER_UID_GID=1000:0
NGINX_UID_GID=101:0
# the non-root Nginx image listens on 8080 and 8443 inside the container
NGINX_HTTP_LISTEN_PORT=8080
NGINX_HTTPS_LISTEN_PORT=8443
```

In `GEOSERVER_JAVA_OPTS`, write the JVM log to the data directory, a non-root GeoServer cannot write to `/var/log`:

```bash
-XX:LogFile=/geoserver_data/data/logs/jvm.log
```

**4. Stop the stack**, keeping the volumes:

```bash
docker compose down
```

!!! warning
    Do not add `-v`: it deletes the volumes and all the data.

**5. Fix the ownership of the volumes:**

```bash
docker compose run --rm -e PERMISSIONS_INIT_FORCE=true permissions-init
```

**6. Start the stack:**

```bash
docker compose up -d
```

**7. Check the users and the site:**

```bash
for s in django celery geoserver nginx db redis; do echo "$s: $(docker compose exec $s id)"; done
curl -I http://localhost/
```

Expected: `uid=1000 gid=0` for django, celery and geoserver, `uid=101 gid=0` for nginx, `uid=70 gid=70` for db, `uid=999 gid=1000` for redis.

If a service stops with `cannot write to ...` or `Permission denied`, run step 5 again and start it again.

!!! note
    The new Nginx image renders its configuration from templates inside the image. Templates edited in the `nginx-confd` volume (`nginx.conf.envsubst`, `sites-enabled/geonode.conf.envsubst`, `nginx.https.available.conf.envsubst`) are ignored: copy them to `/etc/nginx/templates/` in the same volume to keep them. Certificates in the `nginx-certificates` volume are not affected.

To go back to root, remove the `*_UID_GID` and `NGINX_*_LISTEN_PORT` variables and `docker-compose.override.yml`, then run `docker compose up -d`. Before switching to non-root again, repeat step 5: files created while running as root belong to root.
