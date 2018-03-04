from django_db_logger.models import StatusLog
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .serializers import LogsSerializer


class LogsListAPIView(ListAPIView):
    queryset = StatusLog.objects.all()
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = LogsSerializer
    