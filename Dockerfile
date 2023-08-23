FROM geonode/geonode-base:latest-ubuntu-22.10
LABEL GeoNode development team

# add bower and grunt command
COPY . /usr/src/geonode/
WORKDIR /usr/src/geonode

#COPY monitoring-cron /etc/cron.d/monitoring-cron
#RUN chmod 0644 /etc/cron.d/monitoring-cron
#RUN crontab /etc/cron.d/monitoring-cron
#RUN touch /var/log/cron.log
#RUN service cron start

COPY wait-for-databases.sh /usr/bin/wait-for-databases
RUN chmod +x /usr/bin/wait-for-databases
RUN chmod +x /usr/src/geonode/tasks.py \
    && chmod +x /usr/src/geonode/entrypoint.sh

COPY celery.sh /usr/bin/celery-commands
RUN chmod +x /usr/bin/celery-commands

COPY celery-cmd /usr/bin/celery-cmd
RUN chmod +x /usr/bin/celery-cmd

# # Install "geonode-contribs" apps
# RUN cd /usr/src; git clone https://github.com/GeoNode/geonode-contribs.git -b master
# # Install logstash and centralized dashboard dependencies
# RUN cd /usr/src/geonode-contribs/geonode-logstash; pip install --upgrade  -e . \
#     cd /usr/src/geonode-contribs/ldap; pip install --upgrade  -e .

RUN yes w | pip install --src /usr/src -r requirements.txt &&\
    yes w | pip install -e .

# Cleanup apt update lists
RUN apt-get autoremove --purge &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/*

# Export ports
EXPOSE 8000

# We provide no command or entrypoint as this image can be used to serve the django project or run celery tasks
# ENTRYPOINT /usr/src/geonode/entrypoint.sh
