import json
import logging
import os

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from wsgiref.util import FileWrapper
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from tasks import send_user_download_link


class DownloadTaskAPIView(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        db_logger = logging.getLogger('db')

        data = request.data
        data = json.loads(data.dict().keys()[0])

        try:
            # 1. send "data" and "request" to celery task
            send_user_download_link(data, request)

        except Exception as e:
            print e

            db_logger.exception(e)

            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class DownloadAPIView(APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request, format=None, file_name=None):

        if file_name != None:  # and request.user.is_authenticated():
            download_file = settings.MEDIA_ROOT + "/exports/" + str(file_name)

            if os.path.isfile(download_file):
                # prepare download file

                zip_file = open(download_file, 'rb')
                response = HttpResponse(FileWrapper(zip_file), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="%s"' % str(file_name)
                return response

            else:
                # Redirect 404 page or not found
                raise Http404()
        else:
            HttpResponseRedirect('/account/login')

        return Response(status=status.HTTP_200_OK)
