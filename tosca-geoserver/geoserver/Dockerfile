FROM geonode/geoserver:2.24.4-latest
COPY  download_plugins.sh .
RUN chmod +x download_plugins.sh \ 
&& ./download_plugins.sh "2.24.4" "mbstyle vectortiles" \
&&  cp -r plugins/* /usr/local/tomcat/webapps/geoserver/WEB-INF/lib
COPY entrypoint.sh  /usr/local/tomcat/tmp/entrypoint.sh
RUN chmod +x /usr/local/tomcat/tmp/entrypoint.sh
CMD ["/usr/local/tomcat/tmp/entrypoint.sh"]
