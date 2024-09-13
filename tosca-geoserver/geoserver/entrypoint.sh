#!/bin/bash
set -e

source /root/.bashrc


INVOKE_LOG_STDOUT=${INVOKE_LOG_STDOUT:-TRUE}
invoke () {
    if [ $INVOKE_LOG_STDOUT = 'true' ] || [ $INVOKE_LOG_STDOUT = 'True' ]
    then
        /usr/local/bin/invoke $@
    else
        /usr/local/bin/invoke $@ > /usr/src/geonode/invoke.log 2>&1
    fi
    echo "$@ tasks done"
}

# control the values of LB settings if present
if [ -n "$GEONODE_LB_HOST_IP" ];
then
    echo "GEONODE_LB_HOST_IP is defined and not empty with the value '$GEONODE_LB_HOST_IP' "
    echo export GEONODE_LB_HOST_IP=${GEONODE_LB_HOST_IP} >> /root/.override_env
else
    echo "GEONODE_LB_HOST_IP is either not defined or empty setting the value to 'django' "
    echo export GEONODE_LB_HOST_IP=django >> /root/.override_env
    export GEONODE_LB_HOST_IP=django
fi

if [ -n "$GEONODE_LB_PORT" ];
then
    echo "GEONODE_LB_HOST_IP is defined and not empty with the value '$GEONODE_LB_PORT' "
    echo export GEONODE_LB_PORT=${GEONODE_LB_PORT} >> /root/.override_env
else
    echo "GEONODE_LB_PORT is either not defined or empty setting the value to '8000' "
    echo export GEONODE_LB_PORT=8000 >> /root/.override_env
    export GEONODE_LB_PORT=8000
fi

if [ -n "$GEOSERVER_LB_HOST_IP" ];
then
    echo "GEOSERVER_LB_HOST_IP is defined and not empty with the value '$GEOSERVER_LB_HOST_IP' "
    echo export GEOSERVER_LB_HOST_IP=${GEOSERVER_LB_HOST_IP} >> /root/.override_env
else
    echo "GEOSERVER_LB_HOST_IP is either not defined or empty setting the value to 'geoserver' "
    echo export GEOSERVER_LB_HOST_IP=geoserver >> /root/.override_env
    export GEOSERVER_LB_HOST_IP=geoserver
fi

if [ -n "$GEOSERVER_LB_PORT" ];
then
    echo "GEOSERVER_LB_PORT is defined and not empty with the value '$GEOSERVER_LB_PORT' "
    echo export GEOSERVER_LB_PORT=${GEOSERVER_LB_PORT} >> /root/.override_env
else
    echo "GEOSERVER_LB_PORT is either not defined or empty setting the value to '8000' "
    echo export GEOSERVER_LB_PORT=8080 >> /root/.override_env
    export GEOSERVER_LB_PORT=8080
fi

# If DATABASE_HOST is not set in the environment, use the default value
if [ -n "$DATABASE_HOST" ];
then
    echo "DATABASE_HOST is defined and not empty with the value '$DATABASE_HOST' "
    echo export DATABASE_HOST=${DATABASE_HOST} >> /root/.override_env
else
    echo "DATABASE_HOST is either not defined or empty setting the value to 'db' "
    echo export DATABASE_HOST=db >> /root/.override_env
    export DATABASE_HOST=db
fi

# If DATABASE_PORT is not set in the environment, use the default value
if [ -n "$DATABASE_PORT" ];
then
    echo "DATABASE_PORT is defined and not empty with the value '$DATABASE_PORT' "
    echo export DATABASE_HOST=${DATABASE_PORT} >> /root/.override_env
else
    echo "DATABASE_PORT is either not defined or empty setting the value to '5432' "
    echo export DATABASE_PORT=5432 >> /root/.override_env
    export DATABASE_PORT=5432
fi

# If GEONODE_GEODATABASE_USER is not set in the environment, use the default value
if [ -n "$GEONODE_GEODATABASE" ];
then
    echo "GEONODE_GEODATABASE is defined and not empty with the value '$GEONODE_GEODATABASE' "
    echo export GEONODE_GEODATABASE=${GEONODE_GEODATABASE} >> /root/.override_env
else
    echo "GEONODE_GEODATABASE is either not defined or empty setting the value '${COMPOSE_PROJECT_NAME}_data' "
    echo export GEONODE_GEODATABASE=${COMPOSE_PROJECT_NAME}_data >> /root/.override_env
    export GEONODE_GEODATABASE=${COMPOSE_PROJECT_NAME}_data
fi

# If GEONODE_GEODATABASE_USER is not set in the environment, use the default value
if [ -n "$GEONODE_GEODATABASE_USER" ];
then
    echo "GEONODE_GEODATABASE_USER is defined and not empty with the value '$GEONODE_GEODATABASE_USER' "
    echo export GEONODE_GEODATABASE_USER=${GEONODE_GEODATABASE_USER} >> /root/.override_env
else
    echo "GEONODE_GEODATABASE_USER is either not defined or empty setting the value '$GEONODE_GEODATABASE' "
    echo export GEONODE_GEODATABASE_USER=${GEONODE_GEODATABASE} >> /root/.override_env
    export GEONODE_GEODATABASE_USER=${GEONODE_GEODATABASE}
fi

# If GEONODE_GEODATABASE_USER is not set in the environment, use the default value
if [ -n "$GEONODE_GEODATABASE_PASSWORD" ];
then
    echo "GEONODE_GEODATABASE_PASSWORD is defined and not empty with the value '$GEONODE_GEODATABASE_PASSWORD' "
    echo export GEONODE_GEODATABASE_PASSWORD=${GEONODE_GEODATABASE_PASSWORD} >> /root/.override_env
else
    echo "GEONODE_GEODATABASE_PASSWORD is either not defined or empty setting the value '${GEONODE_GEODATABASE}' "
    echo export GEONODE_GEODATABASE_PASSWORD=${GEONODE_GEODATABASE} >> /root/.override_env
    export GEONODE_GEODATABASE_PASSWORD=${GEONODE_GEODATABASE}
fi

# If GEONODE_GEODATABASE_SCHEMA is not set in the environment, use the default value
if [ -n "$GEONODE_GEODATABASE_SCHEMA" ];
then
    echo "GEONODE_GEODATABASE_SCHEMA is defined and not empty with the value '$GEONODE_GEODATABASE_SCHEMA' "
    echo export GEONODE_GEODATABASE_SCHEMA=${GEONODE_GEODATABASE_SCHEMA} >> /root/.override_env
else
    echo "GEONODE_GEODATABASE_SCHEMA is either not defined or empty setting the value to 'public'"
    echo export GEONODE_GEODATABASE_SCHEMA=public >> /root/.override_env
    export GEONODE_GEODATABASE_SCHEMA=public
fi

if [ ! -z "${GEOSERVER_JAVA_OPTS}" ]
then
    echo "GEOSERVER_JAVA_OPTS is filled so I replace the value of '$JAVA_OPTS' with '$GEOSERVER_JAVA_OPTS'"
    export JAVA_OPTS=${GEOSERVER_JAVA_OPTS}
fi

# control the value of NGINX_BASE_URL variable
if [ -z `echo ${NGINX_BASE_URL} | sed 's/http:\/\/\([^:]*\).*/\1/'` ]
then
    echo "NGINX_BASE_URL is empty so I'll use the default Geoserver base url"
    echo "Setting GEOSERVER_LOCATION='${SITEURL}'"
    echo export GEOSERVER_LOCATION=${SITEURL} >> /root/.override_env
else
    echo "NGINX_BASE_URL is filled so GEOSERVER_LOCATION='${NGINX_BASE_URL}'"
    echo "Setting GEOSERVER_LOCATION='${NGINX_BASE_URL}'"
    echo export GEOSERVER_LOCATION=${NGINX_BASE_URL} >> /root/.override_env
fi

if [ -n "$SUBSTITUTION_URL" ];
then
    echo "SUBSTITUTION_URL is defined and not empty with the value '$SUBSTITUTION_URL'"
    echo "Setting GEONODE_LOCATION='${SUBSTITUTION_URL}' "
    echo export GEONODE_LOCATION=${SUBSTITUTION_URL} >> /root/.override_env
else
    echo "SUBSTITUTION_URL is either not defined or empty so I'll use the default GeoNode location "
    echo "Setting GEONODE_LOCATION='http://${GEONODE_LB_HOST_IP}:${GEONODE_LB_PORT}' "
    echo export GEONODE_LOCATION=http://${GEONODE_LB_HOST_IP}:${GEONODE_LB_PORT} >> /root/.override_env
fi

# set basic tagname
TAGNAME=( "baseUrl" "authApiKey" )

if ! [ -f ${GEOSERVER_DATA_DIR}/security/auth/geonodeAuthProvider/config.xml ]
then
    echo "Configuration file '$GEOSERVER_DATA_DIR'/security/auth/geonodeAuthProvider/config.xml is not available so it is gone to skip "
else
    # backup geonodeAuthProvider config.xml
    cp ${GEOSERVER_DATA_DIR}/security/auth/geonodeAuthProvider/config.xml ${GEOSERVER_DATA_DIR}/security/auth/geonodeAuthProvider/config.xml.orig
    # run the setting script for geonodeAuthProvider
    /usr/local/tomcat/tmp/set_geoserver_auth.sh ${GEOSERVER_DATA_DIR}/security/auth/geonodeAuthProvider/config.xml ${GEOSERVER_DATA_DIR}/security/auth/geonodeAuthProvider/ ${TAGNAME[@]} > /dev/null 2>&1
fi

# backup geonode REST role service config.xml
cp "${GEOSERVER_DATA_DIR}/security/role/geonode REST role service/config.xml" "${GEOSERVER_DATA_DIR}/security/role/geonode REST role service/config.xml.orig"
# run the setting script for geonode REST role service
/usr/local/tomcat/tmp/set_geoserver_auth.sh "${GEOSERVER_DATA_DIR}/security/role/geonode REST role service/config.xml" "${GEOSERVER_DATA_DIR}/security/role/geonode REST role service/" ${TAGNAME[@]} > /dev/null 2>&1

# set oauth2 filter tagname
TAGNAME=( "cliendId" "clientSecret" "accessTokenUri" "userAuthorizationUri" "redirectUri" "checkTokenEndpointUrl" "logoutUri" )

# backup geonode-oauth2 config.xml
cp ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml.orig
# run the setting script for geonode-oauth2
/usr/local/tomcat/tmp/set_geoserver_auth.sh ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/ "${TAGNAME[@]}" > /dev/null 2>&1

# set global tagname
TAGNAME=( "proxyBaseUrl" )

# backup global.xml
cp ${GEOSERVER_DATA_DIR}/global.xml ${GEOSERVER_DATA_DIR}/global.xml.orig
# run the setting script for global configuration
/usr/local/tomcat/tmp/set_geoserver_auth.sh ${GEOSERVER_DATA_DIR}/global.xml ${GEOSERVER_DATA_DIR}/ ${TAGNAME[@]} > /dev/null 2>&1

# set correct amqp broker url
sed -i -e 's/localhost/rabbitmq/g' ${GEOSERVER_DATA_DIR}/notifier/notifier.xml

# exclude wrong dependencies
sed -i -e 's/xom-\*\.jar/xom-\*\.jar,bcprov\*\.jar/g' /usr/local/tomcat/conf/catalina.properties

# J2 templating for this docker image we should also do it for other configuration files in /usr/local/tomcat/tmp

declare -a geoserver_datadir_template_dirs=("geofence")

for template in in ${geoserver_datadir_template_dirs[*]}; do
    #Geofence templates
    if [ "$template" == "geofence" ]; then
      cp -R /templates/$template/* ${GEOSERVER_DATA_DIR}/geofence

      for f in $(find ${GEOSERVER_DATA_DIR}/geofence/ -type f -name "*.j2"); do
          echo -e "Evaluating template\n\tSource: $f\n\tDest: ${f%.j2}"
          /usr/local/bin/j2 $f > ${f%.j2}
          rm -f $f
      done

    fi
done

# configure CORS (inspired by https://github.com/oscarfonts/docker-geoserver)
# if enabled, this will add the filter definitions
# to the end of the web.xml
# (this will only happen if our filter has not yet been added before)
echo "Starting entrypoint script to configure CORS..."
if [ "${GEOSERVER_CORS_ENABLED}" = "true" ] || [ "${GEOSERVER_CORS_ENABLED}" = "True" ]; then
  if ! grep -q DockerGeoServerCorsFilter "$CATALINA_HOME/webapps/geoserver/WEB-INF/web.xml"; then
    echo "Enable CORS for $CATALINA_HOME/webapps/geoserver/WEB-INF/web.xml"
    sed -i "\:</web-app>:i\\
    <filter>\n\
      <filter-name>DockerGeoServerCorsFilter</filter-name>\n\
      <filter-class>org.apache.catalina.filters.CorsFilter</filter-class>\n\
      <init-param>\n\
          <param-name>cors.allowed.origins</param-name>\n\
          <param-value>*</param-value>\n\
      </init-param>\n\
      <init-param>\n\
          <param-name>cors.allowed.methods</param-name>\n\
          <param-value>GET,POST,HEAD,OPTIONS,PUT</param-value>\n\
      </init-param>\n\
      <init-param>\n\
        <param-name>cors.allowed.headers</param-name>\n\
        <param-value>Content-Type,X-Requested-With,accept,Access-Control-Request-Method,Access-Control-Request-Headers,If-Modified-Since,Range,Origin,Authorization</param-value>\n\
      </init-param>\n\
      <init-param>\n\
        <param-name>cors.exposed.headers</param-name>\n\
        <param-value>Access-Control-Allow-Origin,Access-Control-Allow-Credentials</param-value>\n\
      </init-param>\n\
      <init-param>\n\
        <param-name>cors.support.credentials</param-name>\n\
        <param-value>False</param-value>\n\
      </init-param>\n\
      <init-param>\n\
        <param-name>cors.preflight.maxage</param-name>\n\
        <param-value>10</param-value>\n\
      </init-param>\n\
    </filter>\n\
    <filter-mapping>\n\
      <filter-name>DockerGeoServerCorsFilter</filter-name>\n\
      <url-pattern>/*</url-pattern>\n\
    </filter-mapping>" "$CATALINA_HOME/webapps/geoserver/WEB-INF/web.xml";
  fi
fi
echo "CORS configuration completed."
if [ ${FORCE_REINIT} = "true" ]  || [ ${FORCE_REINIT} = "True" ] || [ ! -e "${GEOSERVER_DATA_DIR}/geoserver_init.lock" ]; then
    # Run async configuration, it needs Geoserver to be up and running
    nohup sh -c "invoke configure-geoserver" &
fi

# start tomcat
exec env JAVA_OPTS="${JAVA_OPTS}" catalina.sh run