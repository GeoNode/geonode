#!/bin/sh

# Exit script in case of error
set -e

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING GEOSERVER ENTRYPOINT -----------------------"
date


############################
# 0. Defining BASEURL
############################

echo "-----------------------------------------------------"
echo "0. Defining BASEURL"

if [ ! -z "$HTTPS_HOST" ]; then
    BASEURL="https://$HTTPS_HOST"
    if [ "$HTTPS_PORT" != "443" ]; then
        BASEURL="$BASEURL:$HTTPS_PORT"
    fi
else
    BASEURL="http://$HTTP_HOST"
    if [ "$HTTP_PORT" != "80" ]; then
        BASEURL="$BASEURL:$HTTP_PORT"
    fi
fi

echo "BASEURL is $BASEURL"

############################
# 1. Initializing Geodatadir
############################

echo "-----------------------------------------------------"
echo "1. Initializing Geodatadir"

if [ "$(ls -A /spcgeonode-geodatadir)" ]; then
    echo 'Geodatadir not empty, skipping initialization...'
else
    echo 'Geodatadir empty, we run initialization...'
    cp -rf /data/* /spcgeonode-geodatadir/
fi


############################
# 2. ADMIN ACCOUNT
############################

# This section is not strictly required but allows to login geoserver with the admin account even if OAuth2 is unavailable (e.g. if Django can't start)

echo "-----------------------------------------------------"
echo "2. (Re)setting admin account"

ADMIN_ENCRYPTED_PASSWORD=$(/usr/lib/jvm/java-1.8-openjdk/jre/bin/java -classpath /geoserver-2.14.0/webapps/geoserver/WEB-INF/lib/jasypt-1.9.2.jar org.jasypt.intf.cli.JasyptStringDigestCLI digest.sh algorithm=SHA-256 saltSizeBytes=16 iterations=100000 input="$ADMIN_PASSWORD" verbose=0 | tr -d '\n')
sed -i -r "s|<user enabled=\".*\" name=\".*\" password=\".*\"/>|<user enabled=\"true\" name=\"$ADMIN_USERNAME\" password=\"digest1:$ADMIN_ENCRYPTED_PASSWORD\"/>|" "/spcgeonode-geodatadir/security/usergroup/default/users.xml"
# TODO : more selective regexp for this one as there may be several users...
sed -i -r "s|<userRoles username=\".*\">|<userRoles username=\"$ADMIN_USERNAME\">|" "/spcgeonode-geodatadir/security/role/default/roles.xml"
ADMIN_ENCRYPTED_PASSWORD=""


############################
# 3. OAUTH2 CONFIGURATION
############################

echo "-----------------------------------------------------"
echo "3. (Re)setting OAuth2 Configuration"

# Edit /spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml

# Getting oauth keys and secrets from the database
CLIENT_ID=$(psql -h postgres -U postgres -c "SELECT client_id FROM oauth2_provider_application WHERE name='GeoServer'" -t | tr -d '[:space:]')
CLIENT_SECRET=$(psql -h postgres -U postgres -c "SELECT client_secret FROM oauth2_provider_application WHERE name='GeoServer'" -t | tr -d '[:space:]')
if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo "Could not get OAuth2 ID and SECRET from database. Make sure Postgres container is started and Django has finished it's migrations."
    exit 1
fi

sed -i -r "s|<cliendId>.*</cliendId>|<cliendId>$CLIENT_ID</cliendId>|" "/spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<clientSecret>.*</clientSecret>|<clientSecret>$CLIENT_SECRET</clientSecret>|" "/spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml"
# OAuth endpoints (client)
sed -i -r "s|<userAuthorizationUri>.*</userAuthorizationUri>|<userAuthorizationUri>$BASEURL/o/authorize/</userAuthorizationUri>|" "/spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<redirectUri>.*</redirectUri>|<redirectUri>$BASEURL/geoserver/index.html</redirectUri>|" "/spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<logoutUri>.*</logoutUri>|<logoutUri>$BASEURL/account/logout/</logoutUri>|" "/spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml"
# OAuth endpoints (server)
sed -i -r "s|<accessTokenUri>.*</accessTokenUri>|<accessTokenUri>http://nginx/o/token/</accessTokenUri>|" "/spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<checkTokenEndpointUrl>.*</checkTokenEndpointUrl>|<checkTokenEndpointUrl>http://nginx/api/o/v4/tokeninfo/</checkTokenEndpointUrl>|" "/spcgeonode-geodatadir/security/filter/geonode-oauth2/config.xml"

# Edit /security/role/geonode REST role service/config.xml
sed -i -r "s|<baseUrl>.*</baseUrl>|<baseUrl>http://nginx</baseUrl>|" "/spcgeonode-geodatadir/security/role/geonode REST role service/config.xml" 

CLIENT_ID=""
CLIENT_SECRET=""


############################
# 3. RE(SETTING) BASE URL
############################

echo "-----------------------------------------------------"
echo "4. (Re)setting Baseurl"

sed -i -r "s|<proxyBaseUrl>.*</proxyBaseUrl>|<proxyBaseUrl>$BASEURL</proxyBaseUrl>|" "/spcgeonode-geodatadir/global.xml" 



echo "-----------------------------------------------------"
echo "FINISHED GEOSERVER ENTRYPOINT -----------------------"
echo "-----------------------------------------------------"

# Run the CMD 
exec "$@"
