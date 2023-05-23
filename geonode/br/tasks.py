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

from typing import List

from django.conf import settings
from django.core.mail import EmailMessage

from geonode.celery_app import app


@app.task(
    bind=True,
    name="geonode.br.tasks.restore_notification",
    queue="email",
    expires=30,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False,
)
def restore_notification(self, recipients: List, backup_file: str, backup_md5: str, exception: str = None):
    """
    Function sending a CC email report of the restore procedure to a provided emails.
    """
    if exception:
        subject = "Geonode restore procedure FAILED."
        message = (
            f'Restoration of the backup file: "{backup_file}" (MD5 hash: {backup_md5}) on the '
            f"GeoNode instance: {settings.SITEURL} FAILED with an exception: {exception}"
        )
    else:
        subject = "Geonode restore procedure finished with SUCCESS."
        message = (
            f'Restoration of the backup file: "{backup_file}" (MD5 hash: {backup_md5}) on the '
            f"GeoNode instance: {settings.SITEURL} was finished SUCCESSFULLY."
        )

    msg = EmailMessage(subject=subject, body=message, to=recipients)
    msg.send()
