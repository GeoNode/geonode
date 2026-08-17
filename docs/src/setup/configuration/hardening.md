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

# Verify and secure credentials

Credential review applies to every deployment method. For production deployments, complete this check before exposing the instance publicly. If `.env` was generated with `create-envfile.py`, double check that the generated random admin passwords, OAuth2 client credentials, and OAuth2 API key are the values you intend to use. If `.env` was created manually or copied from a sample, replace any default passwords, OAuth2 keys, and API keys.

## Verify admin passwords

1. **GeoNode admin password**: Confirm that the GeoNode admin password is not the default value and matches the value you expect from `.env`. If you need to change it, log into your GeoNode instance at `https://my_geonode.geonode.org/admin` and update the admin user password.

2. **GeoServer admin password**: Confirm that the GeoServer admin password is not the default value and matches the value you expect from `.env`. If you need to change it:

    - Log into GeoServer at `https://my_geonode.geonode.org/geoserver`
    - Go to `Security` > `Users, Groups, and Roles` > `Users/Groups`
    - Change the admin user password
    - Update `GEOSERVER_ADMIN_PASSWORD` in `.env` to match the new password
    - Recreate the Django container so GeoNode reloads the updated GeoServer password:

        ```bash
        docker compose up -d django
        ```

## Verify or update OAuth2 keys

Confirm that the OAuth2 client credentials and `OAUTH2_API_KEY` are not empty, default, or sample values. The API key strengthens the endpoints involved in GeoServer and GeoNode authentication, so it should be treated as a secret. Generate new OAuth2 values when they were copied from a sample file or when you need to rotate them:

1. **Generate new OAuth2 values** in your `.env` file:

    ```bash
    OAUTH2_API_KEY=your_new_api_key
    OAUTH2_CLIENT_ID=your_new_client_id
    OAUTH2_CLIENT_SECRET=your_new_client_secret
    ```

2. **Update GeoNode OAuth2 configuration**:

    - Log into your GeoNode admin panel at `https://my_geonode.geonode.org/admin`
    - Navigate to `Django OAuth Toolkit` > `Applications`
    - Find and edit the existing GeoServer application
    - Update `Client id` and `Client secret` to match your new `.env` values
    - Save the changes

3. **Update GeoServer OAuth2 configuration**:

    - Log into GeoServer at `https://my_geonode.geonode.org/geoserver`
    - Go to `Security` > `Authentication` > `Authentication Filters`
    - Edit the `geonode-oauth2` filter
    - Update `Client ID` and `Client Secret` to match your new `.env` values
    - Save the changes

4. **Recreate the containers**:

    ```bash
    docker compose up -d django geoserver
    ```
