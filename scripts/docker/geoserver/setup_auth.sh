#!/bin/sh
sed -i.bak 's@<baseUrl>\([^<][^<]*\)</baseUrl>@<baseUrl>'"$DJANGO_URL"'</baseUrl>@'\
           /geoserver_data/data/security/auth/geonodeAuthProvider/config.xml