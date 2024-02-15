#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import os
import logging

from celery import Celery

# from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")
app = Celery("geonode")
logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(packages=["geonode.harvesting.harvesters"])

""" CELERAY SAMPLE TASKS
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

@app.task(
    bind=True,
    name='geonode.test',
    queue='default')
def test(arg):
    _log(arg)

@app.task(
    bind=True,
    name='geonode.debug_task',
    queue='default')
def debug_task(self):
    _log(f"Request: {self.request}")
"""
