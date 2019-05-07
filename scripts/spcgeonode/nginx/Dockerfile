FROM nginx:1.13.7-alpine

RUN apk add --no-cache openssl inotify-tools

WORKDIR /etc/nginx/

ADD nginx.conf.envsubst nginx.https.available.conf.envsubst spcgeonode.conf ./

ADD docker-autoreload.sh docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
RUN chmod +x /docker-autoreload.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["nginx", "-g", "daemon off;"]