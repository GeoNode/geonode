# Docker Environmental Variables { #dockerenvvars }

This list reports the specific environmental variables required for the configuration and execution of GeoNode Docker services.

## GeoServer

**DATABASE_HOST**

- Default: ``db``

Internal IP or hostname for the PostgreSQL (``db``) Docker container.

**DATABASE_PORT**

- Default: ``django``

Internal port for the PostgreSQL (``db``) Docker container.

**GEONODE_LB_HOST_IP**

- Default: ``django``

Internal IP or hostname for the GeoNode (``django``) Docker container.

**GEONODE_LB_PORT**

- Default: ``8000``

Internal port for the GeoNode (``django``) Docker container.

**GEONODE_GEODATABSE**

- Default: ``geonode_data``

GeoNode geodatabase name.

**GEONODE_GEODATABASE_USER**

- Default: ``geonode_data``

GeoNode geodatabase user.

**GEONODE_GEODATABASE_PASSWORD**

- Default: ``geonode_data``

GeoNode geodatabase password.

**GEONODE_GEODATABASE_SCHEMA**

- Default: ``publix``

GeoNode geodatabase schema.

**GEOSERVER_JAVA_OPTS**

- Default:

```bash
'-Djava.awt.headless=true -Xms4G -Xmx4G -Dgwc.context.suffix=gwc -XX:+UnlockDiagnosticVMOptions -XX:+LogVMOutput -XX:LogFile=/var/log/jvm.log -XX:PerfDataSamplingInterval=500 -XX:SoftRefLRUPolicyMSPerMB=36000 -XX:-UseGCOverheadLimit -XX:ParallelGCThreads=4 -Dfile.encoding=UTF8 -Djavax.servlet.request.encoding=UTF-8 -Djavax.servlet.response.encoding=UTF-8 -Duser.timezone=GMT -Dorg.geotools.shapefile.datetime=false -DGS-SHAPEFILE-CHARSET=UTF-8 -DGEOSERVER_CSRF_DISABLED=true -DPRINT_BASE_URL={geoserver_ui}/geoserver/pdf -DALLOW_ENV_PARAMETRIZATION=true -Xbootclasspath/a:/usr/local/tomcat/webapps/geoserver/WEB-INF/lib/marlin-0.9.3-Unsafe.jar -Dsun.java2d.renderer=org.marlin.pisces.MarlinRenderingEngine'
```

GeoServer JAVA OPTS.

**GEOSERVER_LB_HOST_IP**

- Default: ``geoserver``

Internal IP or hostname for the GeoServer (``geoserver``) Docker container.

**GEOSERVER_LB_PORT**

- Default: ``8080``

Internal port for the GeoServer (``geoserver``) Docker container.

**NGINX_BASE_URL**

- Default: ``http(s):/localhost``

Public URL of the ``nginx`` service. This value must match GeoNode's ``SITEURL`` setting.

**OAUTH2_API_KEY**

- Default: ``(empty)``

Optional API key for the communication between GeoServer and GeoNode OAuth2 services.

**OAUTH2_CLIENT_ID**

- Default: ``(empty)``

GeoServer client ID for the GeoNode OAuth2 server. Cannot be empty.

**OAUTH2_CLIENT_SECRET**

- Default: ``(empty)``

GeoServer client secret for the GeoNode OAuth2 server. Cannot be empty.

## Nginx

**GEONODE_LB_HOST_IP**

- Default: ``django``

Internal IP or hostname for the GeoNode (``django``) Docker container.

**GEONODE_LB_PORT**

- Default: ``8000``

Internal port for the GeoNode (``django``) Docker container.

**GEOSERVER_LB_HOST_IP**

- Default: ``geoserver``

Internal IP or hostname for the GeoServer (``geoserver``) Docker container.

**GEOSERVER_LB_PORT**

- Default: ``8080``

Internal port for the GeoServer (``geoserver``) Docker container.

**HTTPS_HOST**

- Default: ``localhost``

The public hostname for HTTPS, without the ``http:/`` scheme prefix.

**HTTPS_HOST**

- Default: ``localhost``

The public hostname for HTTPS, without the ``https:/`` scheme prefix.

**HTTP_PORT**

- Default: ``80``

Host port on which to expose the Nginx service for HTTP.

**HTTPS_PORT**

- Default: ``443``

Host port on which to expose the Nginx service for HTTPS.

**LETSENCRYPT_MODE**

- Default: ``disabled``

Possible values:

- ``disabled``: SSL disabled
- ``staging``: SSL local cert
- ``production``: SSL released by an ACME server

## PostgreSQL / PostGIS

**GEONODE_DATABASE**

- Default: ``geonode``

GeoNode database name.

**GEONODE_DATABASE_USER**

- Default: ``geonode_data``

GeoNode database user.

**GEONODE_DATABASE_PASSWORD**

- Default: ``geonode_data``

GeoNode database password.

**GEONODE_GEODATABSE**

- Default: ``geonode_data``

GeoNode geodatabase name.

**GEONODE_GEODATABASE_USER**

- Default: ``geonode_data``

GeoNode geodatabase user.

**GEONODE_GEODATABASE_PASSWORD**

- Default: ``geonode_data``

GeoNode geodatabase password.

**POSTGRES_USER**

- Default: ``geonode_data``

PostgreSQL admin user.

**POSTGRES_USER**

- Default: ``geonode_data``

PostgreSQL admin password.
