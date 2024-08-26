ARG BASE_IMAGE_VERSION
FROM tosca-geonode-base:2.24.4

## GeoServer plugins
# Make sure GeoServer container is prepared for each plugin!
# Use further RUN statements to install neccessary dependencies.
# Refer to plugin documentation what is required to use a plugin.
COPY ./plugins /usr/local/tomcat/webapps/geoserver/WEB-INF/lib
CMD ["/usr/local/tomcat/tmp/entrypoint.sh"]
#bu buradayken bir deniyebilirz. bunu aktif ettiğimizde geoserver .env alarak islem yapmasi gerekir