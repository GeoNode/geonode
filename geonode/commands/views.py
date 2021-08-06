#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .tasks import enqueue_jobs
from geonode.permissions import IsSuperUser

class CommandView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        # TODO: This may return a list of user's jobs
        return Response(
                {"message": "yet to be implemented!"},
                status=status.HTTP_200_OK,
            )

    def post(self, request):
        """
        API to enque management commands into Celery as cron jobs

        Expected Payload Format
        {
            "cmd": command name
            "args": [<arg1>, <arg2>],
            "kwargs: {<key1>: <val1>, <key2>: <val2>}
        }

        Example Payload:
        {
        "cmd": "test_command",
        "args": ["delta"],
        "kwargs": {
                "cpair": [10, 40],
                "ppair": ["a", "b"]
            }
        }
        """
        
        args = request.data.get("args", [])
        kwargs = request.data.get("kwargs", {})
        cmd = request.data.get("cmd", None)

        if cmd is None:
            return Response(
                {"success": False, "error": "Invalid Command"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "--help" in args:
            return Response(
                {"success": False, "error": 'Forbidden argument: "--help"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            enqueue_jobs.delay(request.user.username, cmd, *args, **kwargs)
            return Response(
                {"success": True, "message": "Job Queued"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
