#from huey.djhuey.decorators import queue_command, periodic_command, crontab
from celery.schedules import crontab
from celery.task import periodic_task, task
from geonode import settings
from geonode.queue.models import GazetteerUpdateJob, LayerBoundsUpdateJob

__author__ = 'mbertrand'

@periodic_task(run_every=crontab(minute=settings.QUEUE_INTERVAL))
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

@periodic_task(run_every=crontab(minute=settings.QUEUE_INTERVAL))
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
    hglServiceStarter(None,layername)


