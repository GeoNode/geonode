from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import QueryDict
import json

import logging


class DownloadTaskAPIView(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        db_logger = logging.getLogger('db')

        data = request.data
        data = json.loads(data.dict().keys()[0])
        # import pdb;pdb.set_trace()
        # TODO send these tasks to celery task
        # 1. send "data" to celery task
        # 2. 1 year plus timestamp and encrypt with SECRET_KEY
        import time, hashlib
        s = time.time()
        file_name = hashlib.sha224(str(s)).hexdigest()
        # 3.
        try:
            # start task
            print data

        except Exception as e:

            db_logger.exception(e)

            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)
