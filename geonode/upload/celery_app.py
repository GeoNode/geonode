from celery import Celery

"""
Basic Celery app defined for the importer.
It read all the other settings from the django configuration file
so is always aligned to the geonode settings
"""

importer_app = Celery("importer")

importer_app.config_from_object("django.conf:settings", namespace="CELERY")
