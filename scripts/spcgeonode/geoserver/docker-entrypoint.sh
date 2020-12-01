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
export INTERNAL_OAUTH2_BASEURL="${INTERNAL_OAUTH2_BASEURL:=$BASEURL}"
export GEONODE_URL="${GEONODE_URL:=$BASEURL}"
export BASEURL="$BASEURL/geoserver"

echo "INTERNAL_OAUTH2_BASEURL is $INTERNAL_OAUTH2_BASEURL"
echo "GEONODE_URL is $GEONODE_URL"
echo "BASEURL is $BASEURL"

############################
# 1. Initializing Geodatadir
############################

echo "-----------------------------------------------------"
echo "1. Initializing Geodatadir"

if [ "$(ls -A "${GEOSERVER_DATA_DIR}")" ]; then
    echo 'Geodatadir not empty, skipping initialization...'
else
    echo 'Geodatadir empty, we run initialization...'
    cp -rf /data/* "${GEOSERVER_DATA_DIR}"/
fi


############################
# 2. ADMIN ACCOUNT
############################

# This section is not strictly required but allows to login geoserver with the admin account even if OAuth2 is unavailable (e.g. if Django can't start)

echo "-----------------------------------------------------"
echo "2. (Re)setting admin account"

if [[ -z "${EXISTING_DATA_DIR}" ]]; then \
  ADMIN_ENCRYPTED_PASSWORD=$(/usr/lib/jvm/java-1.8-openjdk/jre/bin/java -classpath /geoserver/webapps/geoserver/WEB-INF/lib/jasypt-1.9.2.jar org.jasypt.intf.cli.JasyptStringDigestCLI digest.sh algorithm=SHA-256 saltSizeBytes=16 iterations=100000 input="$ADMIN_PASSWORD" verbose=0 | tr -d '\n')
  sed -i -r "s|<user enabled=\".*\" name=\".*\" password=\".*\"/>|<user enabled=\"true\" name=\"$ADMIN_USERNAME\" password=\"digest1:$ADMIN_ENCRYPTED_PASSWORD\"/>|" "${GEOSERVER_DATA_DIR}/security/usergroup/default/users.xml"
  # TODO : more selective regexp for this one as there may be several users...
  sed -i -r "s|<userRoles username=\".*\">|<userRoles username=\"$ADMIN_USERNAME\">|" "${GEOSERVER_DATA_DIR}/security/role/default/roles.xml"
  ADMIN_ENCRYPTED_PASSWORD=""
fi;



############################
# 3. WAIT FOR POSTGRESQL
############################

echo "-----------------------------------------------------"
echo "3. Wait for PostgreSQL to be ready and initialized"

# Wait for PostgreSQL
set +e
for i in $(seq 60); do
    sleep 10
    echo "$DATABASE_URL -v ON_ERROR_STOP=1 -c SELECT client_id FROM oauth2_provider_application"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT client_id FROM oauth2_provider_application" &>/dev/null && break
done
if [ $? != 0 ]; then
    echo "PostgreSQL not ready or not initialized"
    exit 1
fi
set -e

############################
# 4. OAUTH2 CONFIGURATION
############################

echo "-----------------------------------------------------"
echo "4. (Re)setting OAuth2 Configuration"

# Edit ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml

# Getting oauth keys and secrets from the database
CLIENT_ID=$(psql "$DATABASE_URL" -c "SELECT client_id FROM oauth2_provider_application WHERE name='GeoServer'" -t | tr -d '[:space:]')
CLIENT_SECRET=$(psql "$DATABASE_URL" -c "SELECT client_secret FROM oauth2_provider_application WHERE name='GeoServer'" -t | tr -d '[:space:]')
if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo "Could not get OAuth2 ID and SECRET from database. Make sure Postgres container is started and Django has finished it's migrations."
    exit 1
fi

sed -i -r "s|<cliendId>.*</cliendId>|<cliendId>$CLIENT_ID</cliendId>|" "${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<clientSecret>.*</clientSecret>|<clientSecret>$CLIENT_SECRET</clientSecret>|" "${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml"
# OAuth endpoints (client)
# These must be reachable by user
sed -i -r "s|<userAuthorizationUri>.*</userAuthorizationUri>|<userAuthorizationUri>$GEONODE_URL/o/authorize/</userAuthorizationUri>|" "${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<redirectUri>.*</redirectUri>|<redirectUri>$BASEURL/index.html</redirectUri>|" "${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<logoutUri>.*</logoutUri>|<logoutUri>$GEONODE_URL/account/logout/</logoutUri>|" "${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml"
# OAuth endpoints (server)
# These must be reachable by server (GeoServer must be able to reach GeoNode)
sed -i -r "s|<accessTokenUri>.*</accessTokenUri>|<accessTokenUri>$INTERNAL_OAUTH2_BASEURL/o/token/</accessTokenUri>|" "${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml"
sed -i -r "s|<checkTokenEndpointUrl>.*</checkTokenEndpointUrl>|<checkTokenEndpointUrl>$INTERNAL_OAUTH2_BASEURL/api/o/v4/tokeninfo/</checkTokenEndpointUrl>|" "${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml"

# Edit /security/role/geonode REST role service/config.xml
sed -i -r "s|<baseUrl>.*</baseUrl>|<baseUrl>$GEONODE_URL</baseUrl>|" "${GEOSERVER_DATA_DIR}/security/role/geonode REST role service/config.xml"

CLIENT_ID=""
CLIENT_SECRET=""


############################
# 5. RE(SETTING) BASE URL
############################

echo "-----------------------------------------------------"
echo "5. (Re)setting Baseurl"

sed -i -r "s|<proxyBaseUrl>.*</proxyBaseUrl>|<proxyBaseUrl>$BASEURL</proxyBaseUrl>|" "${GEOSERVER_DATA_DIR}/global.xml"

############################
# 6. IMPORTING SSL CERTIFICATE
############################

echo "-----------------------------------------------------"
echo "6. Importing SSL certificate (if using HTTPS)"

# https://docs.geoserver.org/stable/en/user/community/oauth2/index.html#ssl-trusted-certificates
if [ ! -z "$HTTPS_HOST" ]; then
    # Random password are generated every container restart
    PASSWORD=$(openssl rand -base64 18)
    # Since keystore password are autogenerated every container restart,
    # The same keystore will not be able to be opened again.
    # So, we create a new one.
    rm -f /keystore.jks

    # Support for Kubernetes/Docker file secrets if the certificate file path is defined
    if [ ! -z "${SSL_CERT_FILE}" ]; then
      cp -f ${SSL_CERT_FILE} server.crt
    else
      openssl s_client -connect ${HTTPS_HOST#https://}:${HTTPS_PORT} </dev/null |
          openssl x509 -out server.crt
    fi

    # create a keystore and import certificate
    if [ "$(ls -A /keystore.jks)" ]; then
    echo 'Keystore not empty, skipping initialization...'
    else
    echo 'Keystore empty, we run initialization...'
        keytool -import -noprompt -trustcacerts \
            -alias ${HTTPS_HOST} -file server.crt \
            -keystore /keystore.jks -storepass ${PASSWORD}
    fi
    rm server.crt

    export GEOSERVER_JAVA_OPTS="-Djava.awt.headless=true -Xms${INITIAL_MEMORY} -Xmx${MAXIMUM_MEMORY} \
    -XX:PerfDataSamplingInterval=500 -XX:SoftRefLRUPolicyMSPerMB=36000 \
    -XX:-UseGCOverheadLimit -XX:+UseConcMarkSweepGC -XX:+UseParNewGC -XX:ParallelGCThreads=4 \
    -Dfile.encoding=UTF8 -Djavax.servlet.request.encoding=UTF-8 \
    -Djavax.servlet.response.encoding=UTF-8 -Duser.timezone=GMT \
    -Dorg.geotools.shapefile.datetime=false -DGEOSERVER_CSRF_DISABLED=${GEOSERVER_CSRF_DISABLED} \
    -Djavax.net.ssl.keyStore=/keystore.jks -Djavax.net.ssl.keyStorePassword=$PASSWORD"

    export JAVA_OPTS="$JAVA_OPTS ${GEOSERVER_JAVA_OPTS}"
fi

echo "-----------------------------------------------------"
echo "FINISHED GEOSERVER ENTRYPOINT -----------------------"
echo "-----------------------------------------------------"

# Run the CMD
exec "$@"
