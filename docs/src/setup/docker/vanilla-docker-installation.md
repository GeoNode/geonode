# Vanilla Docker installation

In this section, we are going to list the steps needed to deploy a vanilla **GeoNode** with **Docker**.

### Clone the source code

```bash
cd ~
git clone https://github.com/GeoNode/geonode.git
```

### Prepare the .env file

Navigate to the GeoNode folder and create the .env file by using the `create-envfile` script:

```bash
cd geonode
python create-envfile.py
```
`create-envfile.py` accepts the following arguments:

- `--https`: Enable SSL. It's disabled by default
- `--env_type`: 
    - When set to `prod` `DEBUG` is disabled and the creation of a valid `SSL` is requested to Letsencrypt's ACME server
    - When set to `test`  `DEBUG` is disabled and a test `SSL` certificate is generated for local testing
    - When set to `dev`  `DEBUG` is enabled and no `SSL` certificate is generated
- `--hostname`: The URL that will serve GeoNode (`localhost` by default)
- `--email`: The administrator's email. Notice that a real email and valid SMPT configurations are required if  `--env_type` is set to `prod`. Letsencrypt uses email for issuing the SSL certificate 
- `--geonodepwd`: GeoNode's administrator password. A random value is set if left empty
- `--geoserverpwd`: GeoNode's administrator password. A random value is set if left empty
- `--pgpwd`: PostgreSQL's administrator password. A random value is set if left empty
- `--dbpwd`: GeoNode DB user role's password. A random value is set if left empty
- `--geodbpwd`: GeoNode data DB user role's password. A random value is set if left empty
- `--clientid`: Client id of Geoserver's GeoNode Oauth2 client. A random value is set if left empty
- `--clientsecret`: Client secret of Geoserver's GeoNode Oauth2 client. A random value is set if left empty

### Build and run

Finally, to build and run GeoNode run the following:

```bash
docker compose build
docker compose up -d
```

If the build is successful, you will be able to navigate on GeoNode project at `http://localhost`

### Login as an administrator on GeoNode

To connect on the GeoNode project as administrator, use the credentials from the `.env` file:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD={geonodepwd}
```

### Test the instance and follow the logs

If you run the containers daemonized (with the `-d` option), you can either run specific Docker commands to follow the ``startup and initialization logs`` or entering the image `shell` and check for the `GeoNode logs`.

In order to follow the `startup and initialization logs`, you will need to run the following command from the repository folder

```bash
cd ~/geonode
docker logs -f django4geonode
```

Alternatively:

```bash
cd ~/geonode
docker compose logs -f django
```
You should be able to see several initialization messages. Once the container is up and running, you will see the following statements

```bash
...
789 static files copied to '/mnt/volumes/statics/static'.
static data refreshed
Executing UWSGI server uwsgi --ini /usr/src/app/uwsgi.ini for Production
[uWSGI] getting INI configuration from /usr/src/app/uwsgi.ini
```

To exit just hit `CTRL+C`.

This message means that the GeoNode containers have been started. Browsing to `http://localhost/` will show the GeoNode home page. You should be able to successfully log with the credentials of admin user which are defined in the .env file and start using it right away.

With Docker it is also possible to run a shell in the container and follow the logs exactly the same as you deployed it on a physical host. To achieve this run

```bash
docker exec -it django4geonode /bin/bash
# Once logged in the GeoNode image, follow the logs by executing
tail -F -n 300 /var/log/geonode.log
```

### Override the ENV variables to deploy on a public IP or domain

If you would like to start the containers on a `public IP` or `domain`, let's say `https://my_geonode.geonode.org/`, you can follow the instructions below:

```bash
DOCKER_ENV=production
SITEURL=https://my_geonode.geonode.org/
NGINX_BASE_URL=https://my_geonode.geonode.org/
ALLOWED_HOSTS=['django',]
GEOSERVER_WEB_UI_LOCATION=https://my_geonode.geonode.org/geoserver/
GEOSERVER_PUBLIC_LOCATION=https://my_geonode.geonode.org/geoserver/
HTTP_HOST=
HTTPS_HOST=my_geonode.geonode.org
HTTP_PORT=80
HTTPS_PORT=443
LETSENCRYPT_MODE=production # This will use Letsencrypt and the ACME server to generate valid SSL certificates
```

These variables are automatically set by the `create-envfile.py` script if the `--https` and `--hostname` variables are used.

!!! warning 
    When `LETSENCRYPT_MODE` is set to production a valid email and email SMPT server are required to make the system generate a valid certificate.

Whenever you change someting on .env file, you will need to rebuild the containers:

```bash
docker-compose up -d
```

!!! Note 
    This command drops any change you might have done manually inside the containers, except for the static volumes.

### Remove all data and bring your running GeoNode deployment to the initial stage

This action allows you to stop all the containers and reset all the data with the deletion of all the volumes. 

!!! warning
    The following command should be used with caution because it will delete all the data included in the instance

```bash
cd ~/geonode
# stop containers and remove volumes
docker-compose down -v
```


