FROM geonode/geonode:latest
LABEL GeoNode development team

COPY requirements.txt /usr/src/app/
RUN pip install pip --upgrade
RUN pip install -r requirements.txt --upgrade

WORKDIR /usr/src/geonode/
RUN git pull
RUN pip install -e . --upgrade

# Activate "memcached"
RUN apt install -y cron memcached
RUN pip install pylibmc \
    && pip install sherlock

RUN python manage.py makemigrations --settings=geonode.settings
RUN python manage.py migrate --settings=geonode.settings

EXPOSE 8000

ENTRYPOINT service cron restart && service memcached restart && /usr/src/app/entrypoint.sh
