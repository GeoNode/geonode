FROM geonode/geonode:latest
MAINTAINER GeoNode development team

COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --upgrade
RUN python manage.py makemigrations --settings=geonode.settings
RUN python manage.py migrate --settings=geonode.settings

EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["paver", "start_django", "-b", "0.0.0.0:8000"]
CMD ["uwsgi", "--ini", "uwsgi.ini"]
