FROM alpine:3.6

# Install deps
RUN apk add --no-cache libressl ca-certificates gettext

# Install rclone
RUN wget https://downloads.rclone.org/v1.40/rclone-v1.40-linux-amd64.zip
RUN unzip /rclone-v1.40-linux-amd64.zip
RUN mv /rclone-v1.40-linux-amd64/rclone /usr/bin
RUN rm /rclone-v1.40-linux-amd64.zip
RUN rm -rf /rclone-v1.40-linux-amd64


# Add scripts
ADD sync.sh /root/sync.sh
RUN chmod +x /root/sync.sh

ADD docker-entrypoint.sh docker-entrypoint.sh
RUN chmod +x docker-entrypoint.sh

ADD crontab crontab 
RUN /usr/bin/crontab crontab
RUN rm crontab

ADD rclone.s3.conf.envsubst rclone.s3.conf.envsubst

# We run cron in foreground to update the certificates
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/sbin/crond", "-f"]
