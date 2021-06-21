#########################################################################
#
# Copyright (C) 2017 OSGeo
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
import logging

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_noop as _

from geonode.utils import parse_datetime
from geonode.monitoring.utils import TypeChecks, collect_metric

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Run collecting for monitoring
    """

    def add_arguments(self, parser):
        parser.add_argument('-l', '--list', dest='list_services', action='store_true', default=False,
                            help=_("Show list of services"))
        parser.add_argument('-s', '--since', dest='since', default=None, type=parse_datetime,
                            help=_("Process data since specific timestamp (YYYY-MM-DD HH:MM:SS format). "
                                   "If not provided, last sync will be used."))
        parser.add_argument('-u', '--until', dest='until', default=None, type=parse_datetime,
                            help=_("Process data until specific timestamp (YYYY-MM-DD HH:MM:SS format). "
                                   "If not provided, now will be used."))
        parser.add_argument('-f', '--force', dest='force_check', action='store_true', default=False,
                            help=_("Force check"))
        parser.add_argument('-t', '--format', default=TypeChecks.AUDIT_TYPE_JSON, type=TypeChecks.audit_format,
                            help=_("Format of audit log (xml, json)"))
        parser.add_argument('-k', '--do-not-clear', default=False, action='store_true', dest='do_not_clear',
                            help=_("Should old data be preserved (default: no, "
                                   "data older than settings.MONITORING_DATA_TTL will be removed)"))
        parser.add_argument('-e', '--halt', default=False, action='store_true', dest='halt_on_errors',
                            help=_("Should stop on first error occured (default: no)"))
        parser.add_argument('-n', '--emit_notifications', default=False, action='store_true', dest='emit_notifications',
                            help=_("Should process and send notifications as well (default: no)"))
        parser.add_argument('service', type=TypeChecks.service_type, nargs="?",
                            help=_("Collect data from this service only"))

    def handle(self, *args, **options):
        collect_metric(**options)
