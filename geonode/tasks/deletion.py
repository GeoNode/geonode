from geonode.layers.models import Layer
from geonode.maps.models import Map
from celery.task import task


@task(name='geonode.tasks.deletion.delete_layer', queue='cleanup')
def delete_layer(object_id):
    """
    Deletes a layer.
    """
    try:
        layer = Layer.objects.get(id=object_id)
    except Layer.DoesNotExist:
        return

    layer.delete()


@task(name='geonode.tasks.deletion.delete_map', queue='cleanup', expires=300)
def delete_map(object_id):
    """
    Deletes a map and the associated map layers.
    """

    try:
        map_obj = Map.objects.get(id=object_id)
    except Map.DoesNotExist:
        return

    map_obj.layer_set.all().delete()
    map_obj.delete()
