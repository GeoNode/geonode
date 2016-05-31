FROM ubuntu:14.04

RUN \
  apt-get update && \
  apt-get install -y build-essential && \
  apt-get install -y libxml2-dev libxslt1-dev libjpeg-dev gettext git python-dev python-pip && \
  apt-get install -y python-pillow python-lxml python-psycopg2 python-django python-bs4 python-multipartposthandler transifex-client python-paver python-nose python-django-nose python-gdal python-django-pagination python-django-jsonfield python-django-extensions python-django-taggit python-httplib2 && \
  apt-get install -y --force-yes openjdk-6-jdk ant maven2 --no-install-recommends

WORKDIR /geonode
ADD . /geonode

RUN pip install -e /geonode
RUN paver setup

CMD ["paver", "start", "-b 0.0.0.0:8000","-f"]
EXPOSE 8000
EXPOSE 8080
