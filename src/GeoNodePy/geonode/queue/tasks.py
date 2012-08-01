#from huey.djhuey.decorators import queue_command, periodic_command, crontab
from celery.task.schedules import crontab
from celery.decorators import periodic_task, task
from models import *

__author__ = 'mbertrand'

@periodic_task(run_every=crontab(minute='*/5'))
def updateGazetteer():
    print "start updateGazetteer"
    gazetteerJobs = GazetteerUpdateJob.objects.all()
    for job in gazetteerJobs:
        try:
            print "update gazetteer for " + job.layer.name
            job.layer.update_gazetteer()
            job.delete()
        except Exception, e:
            print e
            job.status = 'failed'
            job.save()
    #print "end updateGazetteer"

@periodic_task(run_every=crontab(minute='*/5'))
def updateBounds():
    boundsJobs = LayerBoundsUpdateJob.objects.all()
    for job in boundsJobs:
        try:
            job.layer.update_bounds()
            job.delete()
        except Exception, e:
            print e
            job.status = 'failed'
            job.save()

@task
def loadHGL(layername):
    from geonode.proxy.views import hglServiceStarter
    try:
        hglServiceStarter(None,layername)
    except Exception, e:
            print e
