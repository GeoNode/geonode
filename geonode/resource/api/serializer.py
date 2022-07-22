
from geonode.base.api.serializers import BaseDynamicModelSerializer
from geonode.resource.models import ExecutionRequest


class ExecutionRequestSerializer(BaseDynamicModelSerializer):

    class Meta:
        model = ExecutionRequest
        name = 'request'
        fields = '__all__'
        view_name = 'executionrequest-list'
