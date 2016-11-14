from tastypie.resources import ModelResource

from geonode.actions.models import Action


class ActionLayerDeleteResource(ModelResource):

    class Meta:
        queryset = Action.objects.filter(action_type='layer_delete').order_by('-timestamp')
        allowed_methods = ['get', ]
        fields = ['args', 'timestamp']
        ordering = ['timestamp', ]
