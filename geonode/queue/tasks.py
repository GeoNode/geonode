#from huey.djhuey.decorators import queue_command, periodic_command, crontab
from celery.schedules import crontab
from celery.task import periodic_task, task
from geonode.settings import settings
from geonode.queue.models import GazetteerUpdateJob


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


@task
def loadHGL(layername):
    from geonode.proxy.views import hglServiceStarter
    hglServiceStarter(None,layername)


