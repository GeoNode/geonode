#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from django.conf import settings
from django.core.mail import EmailMessage

from geonode.celery_app import app


@app.task(queue='email')
def restore_notification(recipients, backup_file, backup_md5, exception=None):
    """
    Function sending a CC email report of the restore procedure to a provided emails.
    """

    if exception:
        subject = 'Geonode restore procedure FAILED.'
        message = 'Restoration of the backup file: "{}" (MD5 hash: {}) on ' \
                  'the GeoNode instance: {} FAILED with an exception: {}'.format(
            backup_file, backup_md5, settings.SITEURL, exception
        )
    else:
        subject = 'Geonode restore procedure finished with SUCCESS.'
        message = 'Restoration of the backup file: "{}" (MD5 hash: {}) on ' \
                  'the GeoNode instance: {} was finished SUCCESSFULLY.'.format(
            backup_file, backup_md5, settings.SITEURL
        )

    msg = EmailMessage(subject=subject, body=message, to=recipients)
    msg.send()
