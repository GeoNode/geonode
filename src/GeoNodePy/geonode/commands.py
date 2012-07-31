from huey.djhuey.decorators import periodic_command, crontab
from geonode.gazetteer.models import GazetteerUpdateJob

__author__ = 'mbertrand'

from celery.task.schedules import crontab
from celery.decorators import periodic_task

# this will run every hour, see http://celeryproject.org/docs/reference/celery.task.schedules.html#celery.task.schedules.crontab
#@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
@periodic_command(crontab(minute='*'))
def updateGazetteer():
    print "FU"
#    gazetteerJobs = GazetteerUpdateJob.objects.all()
#    for job in gazetteerJobs:
#        try:
#            job.layer.update_gazetteer()
#            job.delete()
#            print "Completed job for " +  job.layer.name
#        except:
#            job.status = 'failed'
#            job.save()
#    print "Mission accomplished"
