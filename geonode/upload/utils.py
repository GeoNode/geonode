import enum
from geonode.resource.manager import ResourceManager
from geonode.geoserver.manager import GeoServerResourceManager
from geonode.base.models import ResourceBase
from django.utils.translation import gettext_lazy as _


class ImporterRequestAction(enum.Enum):
    ROLLBACK = _("rollback")


def error_handler(exc, exec_id=None):
    return f'{str(exc.detail if hasattr(exc, "detail") else exc.args[0])}. Request: {exec_id}'


class ImporterConcreteManager(GeoServerResourceManager):
    """
    The default GeoNode concrete manager, handle the communication with geoserver
    For this implementation the interaction with geoserver is not needed
    so we are going to overwrite the concrete manager to avoid it
    """

    def copy(self, instance, uuid, defaults):
        return ResourceBase.objects.get(uuid=uuid)

    def update(self, uuid, **kwargs) -> ResourceBase:
        return ResourceBase.objects.get(uuid=uuid)


custom_resource_manager = ResourceManager(concrete_manager=ImporterConcreteManager())


def call_rollback_function(
    execution_id,
    handlers_module_path,
    prev_action,
    layer=None,
    alternate=None,
    error=None,
    **kwargs,
):
    from geonode.upload.celery_tasks import import_orchestrator

    task_params = (
        {},
        execution_id,
        handlers_module_path,
        "start_rollback",
        layer,
        alternate,
        ImporterRequestAction.ROLLBACK.value,
    )
    kwargs["previous_action"] = prev_action
    kwargs["error"] = error_handler(error, exec_id=execution_id)
    import_orchestrator.apply_async(task_params, kwargs)


def find_key_recursively(obj, key):
    """
    Celery (unluckly) append the kwargs for each task
    under a new kwargs key, so sometimes is faster
    to look into the key recursively instead of
    parsing the dict
    """
    if key in obj:
        return obj.get(key, None)
    for _unsed, v in obj.items():
        if isinstance(v, dict):
            return find_key_recursively(v, key)
