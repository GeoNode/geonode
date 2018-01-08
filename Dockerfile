FROM geonode/geonode:2.6.x
MAINTAINER GeoNode development team

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
