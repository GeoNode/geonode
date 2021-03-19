FROM geonode/geonode:3.1
LABEL GeoNode development team

COPY . /usr/src/app/
WORKDIR /usr/src/app/
# Install pip packages
RUN pip install pip --upgrade
RUN pip install --upgrade --no-cache-dir  --src /usr/src -r requirements.txt \
    && pip install pygdal==$(gdal-config --version).* \
    && pip install flower==0.9.4

RUN pip install --upgrade  -e .

# Activate "memcached"
RUN apt install memcached
RUN pip install pylibmc \
    && pip install sherlock

RUN python manage.py makemigrations --settings=geonode.settings
RUN python manage.py migrate --settings=geonode.settings

# Export ports
EXPOSE 8000

# We provide no command or entrypoint as this image can be used to serve the django project or run celery tasks
ENTRYPOINT service cron restart && service memcached restart && /usr/src/app/entrypoint.sh
