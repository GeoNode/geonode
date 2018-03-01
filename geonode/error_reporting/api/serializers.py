from rest_framework.serializers import ModelSerializer
from django_db_logger.models import StatusLog


class LogsSerializer(ModelSerializer):
    class Meta:
        model = StatusLog
        fields = '__all__'