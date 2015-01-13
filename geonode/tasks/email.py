from celery.task import task
from django.conf import settings
from django.core.mail import send_mail


@task(name='geonode.tasks.email.send_queued_notifications', queue='email')
def send_queued_notifications(*args):
    """
    Sends queued notifications.

    settings.NOTIFICATION_QUEUE_ALL needs to be true in order to take advantage of this.
    """

    try:
        from notification.engine import send_all
    except ImportError:
        return

    # Make sure the application can write to the location where lock files are stored.
    if not args and getattr(settings, 'NOTIFICATION_LOCK_LOCATION', None):
        send_all(settings.NOTIFICATION_LOCK_LOCATION)
    else:
        send_all(*args)


@task(name='geonode.tasks.email.send_email', queue='email')
def send_email(*args, **kwargs):
    """
    Sends an email using django's send_mail functionality.
    """

    send_mail(*args, **kwargs)
