# -*- coding: utf-8 -*-
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
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

from geonode.notifications_helper import NotificationsAppConfigBase, has_notifications
from geonode.contrib.monitoring.models import populate

log = logging.getLogger(__name__)


class MonitoringAppConfig(NotificationsAppConfigBase):
    name = 'geonode.contrib.monitoring'
    NOTIFICATION_NAME = 'monitoring_alert'
    NOTIFICATIONS = ((NOTIFICATION_NAME,
                      _("Monitoring alert"),
                      _("Alert situation reported by monitoring"),
                     ),
                    )

    def run_setup_hooks(self, *args, **kwargs):
        if not has_notifications:
            log.warning("Monitoring requires notifications app to be enabled. "
                        "Otherwise, no notifications will be send")
        populate()

    def ready(self):
        super(MonitoringAppConfig, self).ready()
        signals.post_migrate.connect(self.run_setup_hooks, sender=self)


default_app_config = 'geonode.contrib.monitoring.MonitoringAppConfig'
