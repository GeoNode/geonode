from django.core.management.base import BaseCommand

from ... import models


class Command(BaseCommand):
    args = ''
    help = u"Clean SessionTicket and ProxyGrantingTicket linked to expired sessions"

    def handle(self, *args, **options):
        models.ProxyGrantingTicket.clean_deleted_sessions()
        models.SessionTicket.clean_deleted_sessions()
