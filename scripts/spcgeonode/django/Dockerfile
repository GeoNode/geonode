# TODO : use python:2.7.13-alpine3.6 to make this lighter ( it is what we use for letsencryipt as well)
# But it seems it's not possible for now because alpine only has geos 3.6 which is not supported by django 1.8
# (probably because of https://code.djangoproject.com/ticket/28441)

FROM python:2.7.14-slim-stretch

# Install system dependencies
RUN echo "Updating apt-get" && \
    apt-get update && \
    echo "Installing build dependencies" && \
    apt-get install -y gcc make libc-dev musl-dev libpcre3 libpcre3-dev g++ && \
    echo "Installing Pillow dependencies" && \
    # RUN apt-get install -y NOTHING ?? It was probably added in other packages... ALPINE needed jpeg-dev zlib-dev && \
    echo "Installing GDAL dependencies" && \
    apt-get install -y libgeos-dev libgdal-dev && \
    echo "Installing Psycopg2 dependencies" && \
    # RUN apt-get install -y NOTHING ?? It was probably added in other packages... ALPINE needed postgresql-dev && \
    echo "Installing other dependencies" && \
    apt-get install -y libxml2-dev libxslt-dev && \
    echo "Installing GeoIP dependencies" && \
    apt-get install -y geoip-bin geoip-database && \
    echo "Installing healthceck dependencies" && \
    apt-get install -y curl && \
    echo "Python server" && \
    pip install uwsgi && \
    echo "Removing build dependencies and cleaning up" && \
    # TODO : cleanup apt-get with something like apt-get -y --purge autoremove gcc make libc-dev musl-dev libpcre3 libpcre3-dev g++ && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ~/.cache/pip

# Install python dependencies
RUN echo "Geonode python dependencies"
RUN pip install pygdal==$(gdal-config --version).*
RUN pip install celery==4.1.0 # see https://github.com/GeoNode/geonode/pull/3714

# Install geonode dependencies
ADD requirements.txt /requirements.txt
RUN pip install -r requirements.txt
RUN rm requirements.txt

# Install geonode
RUN mkdir /spcgeonode
WORKDIR /spcgeonode/
ADD . /spcgeonode/
RUN pip install -e .
RUN chmod +x scripts/spcgeonode/django/docker-entrypoint.sh

# Export ports
EXPOSE 8000

# Set environnment variables
ENV PYTHONPATH=/spcgeonode/scripts/spcgeonode/django:$PYTHONPATH
ENV DJANGO_SETTINGS_MODULE=settings_spcgeonode
ENV DATABASE_URL=postgres://postgres:postgres@postgres:5432/postgres
ENV BROKER_URL=amqp://guest:guest@rabbitmq:5672/
ENV STATIC_ROOT=/spcgeonode-static/
ENV MEDIA_ROOT=/spcgeonode-media/
ENV STATIC_URL=/static/
ENV MEDIA_URL=/uploaded/
# TODO : we should probably remove this and set Celery to use JSON serialization instead of pickle
ENV C_FORCE_ROOT=True

# We get an exception after migrations on startup (it seems the monitoring app tries to resolve the geoserver domain name after it's migration, which can happen before oauth migrations on which geoserver startup depends...)
ENV MONITORING_ENABLED=False

# We provide no command or entrypoint as this image can be used to serve the django project or run celery tasks
