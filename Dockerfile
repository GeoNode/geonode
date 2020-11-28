FROM geonode/geonode:3.1
LABEL GeoNode development team

COPY . /usr/src/app/
RUN pip install pip --upgrade; pip install -r requirements.txt --upgrade

WORKDIR /usr/src/geonode/
RUN git reset --hard origin/3.x; git pull; pip install -e . --upgrade

# Activate "memcached"
RUN apt install memcached
RUN pip install pylibmc \
    && pip install sherlock
RUN python manage.py makemigrations --settings=geonode.settings
RUN python manage.py migrate --settings=geonode.settings

EXPOSE 8000

ENTRYPOINT service cron restart && service memcached restart && /usr/src/app/entrypoint.sh
