# Troubleshooting and Advanced Features

## Common Issues and Fixes

- GeoServer/GeoNode OAuth2 does not authenticate as Administrator even using GeoNode `admin` users

    **Symptoms**

    When trying to authenticate with an `admin` user using OAuth2, the process correctly redirects to GeoServer page but I'm not a GeoServer Administrator.

    **Cause**

    That means that somehow GeoServer could not successfully complete the Authorization and Authentication process.

    The possible causes of the problem may be the following ones:

    1. The OAuth2 Authentication fails on GeoServer side

        This is usually due to an exception while trying to complete the Authentication process.

        - A typical cause is that GeoServer tries to use HTTPS connections but the GeoNode certificate is not trusted;

            In that case please refer to the section below. Also take a look at the logs, in particular the GeoServer one.
            The GeoServer logs should contain a detailed Exception explaining the cause of the problem.
            If no exception is listed here, even after the log level has been raised to `DEBUG`, try to check for the GeoNode Role Service as explained below.

        - Another possible issue is that somehow the OAuth2 handshake cannot complete successfully;

            1. Login into GeoServer as administrator through its WEB login form.

            2. Double check that all the `geonode-oauth2 - Authentication using a GeoNode OAuth2` parameters are correct. If everything is ok, take a look at the logs, in particular the GeoServer one.
               The GeoServer logs should contain a detailed Exception explaining the cause of the problem. If no exception is listed here, even after the log level has been raised to `DEBUG`, try to check for the GeoNode Role Service as explained below.

    2. GeoServer is not able to retrieve the user Role from a Role Service

        Always double check both HTTP Server and GeoServer logs. This might directly guide you to the cause of the problem.

        - Check that the GeoServer host is granted to access GeoNode Role Service REST APIs in the `AUTH_IP_WHITELIST` of the `settings.py`
        - Check that the `geonode REST role service` is the default Role service and that the GeoServer OAuth2 Plugin has been configured to use it by default
        - Check that the GeoNode REST Role Service APIs are functional and produce correct JSON.

            This is possible by using simple `cUrl` GET calls like

            ```bash
            curl http://localhost/api/adminRole
            # {"adminRole": "admin"}

            curl http://localhost/api/users
            # {"users": [{"username": "AnonymousUser", "groups": ["anonymous"]}, {"username": "afabiani", "groups": ["anonymous", "test"]}, {"username": "admin", "groups": ["anonymous", "test", "admin"]}]}

            curl http://localhost/api/roles
            # {"groups": ["anonymous", "test", "admin"]}

            curl http://localhost/api/users/admin
            # {"users": [{"username": "admin", "groups": ["anonymous", "test", "admin"]}]}
            ```

## How to setup `HTTPS` secured endpoints

In a production system it is a good practice to encrypt the connection between GeoServer and GeoNode. That would be possible by enabling HTTPS Protocol on the GeoNode REST Role Service APIs and OAuth2 Endpoints.

Most of the times you will rely on a self-signed HTTPS connection using a generated certificate. That makes the connection *untrusted* and you will need to tell the GeoServer Java Virtual Machine to trust it.

This can be done by following the steps below.

For any issue take a look at the logs, in particular the GeoServer one. The GeoServer logs should contain a detailed Exception explaining the cause of the problem.
