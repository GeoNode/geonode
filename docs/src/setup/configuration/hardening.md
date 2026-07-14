# Publish on other than HTTP port (for e.g. 8082)

By default GeoNode will be installed on port `80`, that is HTTP. But what if you want to change the port of GeoNode to something other than the HTTP port? For this example, we are using port `8082`.

We need to edit a couple of things in the web configuration.

First, update the `/etc/uwsgi/apps-enabled/geonode.ini` file:

```bash
sudo vi /etc/uwsgi/apps-enabled/geonode.ini
```

Edit the following lines:

```bash
env = SITE_HOST_NAME=localhost:8082
env = SITEURL=http://localhost:8082

SITE_HOST_NAME=localhost
SITE_HOST_PORT=8082
GEOSERVER_WEB_UI_LOCATION=http://localhost:8082/geoserver/
GEOSERVER_PUBLIC_LOCATION=http://localhost:8082/geoserver/
```

After that, update the `/etc/nginx/sites-enabled/geonode` file:

```bash
sudo vi /etc/nginx/sites-enabled/geonode
```

Edit the following lines:

```bash
server {
    listen 8082 default_server;
    listen [::]:8082 default_server;
```
