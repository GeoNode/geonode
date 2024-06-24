from abc import ABC
import logging
from typing import List

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.layers.models import Dataset
from geonode.upload.api.exception import ImportException
from geonode.upload.utils import ImporterRequestAction as ira
from django_celery_results.models import TaskResult
from django.db.models import Q

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """
    Base abstract handler object
    define the required method needed to define an upload handler
    it must be:
    - provide the tasks list to complete the import
    - validation function
    - method to import the resource
    - create_error_log
    """

    REGISTRY = []

    ACTIONS = {
        exa.IMPORT.value: (),
        exa.COPY.value: (),
        exa.DELETE.value: (),
        exa.UPDATE.value: (),
        ira.ROLLBACK.value: (),
    }

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def register(cls):
        BaseHandler.REGISTRY.append(cls)

    @classmethod
    def get_registry(cls):
        return BaseHandler.REGISTRY

    @classmethod
    def get_task_list(cls, action) -> tuple:
        if action not in cls.ACTIONS:
            raise Exception("The requested action is not implemented yet")
        return cls.ACTIONS.get(action)

    @property
    def default_geometry_column_name(self):
        return "geometry"

    @property
    def id(self):
        pk = self.supported_file_extension_config.get("id", None)
        if pk is None:
            raise ImportException(
                "PK must be defined, check that supported_file_extension_config had been correctly defined, it cannot be empty"
            )
        return pk

    @property
    def supported_file_extension_config(self):
        return {}

    @property
    def can_handle_xml_file(self) -> bool:
        """
        True or false if the handler is able to handle XML file
        By default a common workflow is always defined
        To be override if some expection are needed
        """
        return True

    @property
    def can_handle_sld_file(self) -> bool:
        """
        True or false if the handler is able to handle SLD file
        By default a common workflow is always defined
        To be override if some expection are needed
        """
        return True

    @staticmethod
    def is_valid(files, user):
        """
        Define basic validation steps
        """
        return NotImplementedError

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        return False

    @staticmethod
    def has_serializer(_data) -> bool:
        """
        This endpoint should return (if set) the custom serializer used in the API
        to validate the input resource
        """
        return None

    @staticmethod
    def can_do(action) -> bool:
        """
        Evaluate if the handler can take care of a specific action.
        Each action (import/copy/etc...) can define different step so
        the Handler must be ready to handle them. If is not in the actual
        flow the already in place flow is followd
        """
        return action in BaseHandler.ACTIONS

    @staticmethod
    def extract_params_from_data(_data):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        return []

    @staticmethod
    def perform_last_step(execution_id):
        """
        Override this method if there is some extra step to perform
        before considering the execution as completed.
        For example can be used to trigger an email-send to notify
        that the execution is completed
        """
        from geonode.upload.orchestrator import orchestrator
        from geonode.upload.models import ResourceHandlerInfo

        # as last step, we delete the celery task to keep the number of rows under control
        lower_exec_id = execution_id.replace("-", "_").lower()
        TaskResult.objects.filter(
            Q(task_args__icontains=lower_exec_id)
            | Q(task_kwargs__icontains=lower_exec_id)
            | Q(result__icontains=lower_exec_id)
            | Q(task_args__icontains=execution_id)
            | Q(task_kwargs__icontains=execution_id)
            | Q(result__icontains=execution_id)
        ).delete()

        _exec = orchestrator.get_execution_object(execution_id)

        resource_output_params = [
            {"detail_url": x.resource.detail_url, "id": x.resource.pk}
            for x in ResourceHandlerInfo.objects.filter(execution_request=_exec)
        ]
        _exec.output_params.update({"resources": resource_output_params})
        _exec.save()

        return _exec

    def fixup_name(self, name):
        """
        Emulate the LAUNDER option in ogr2ogr which will normalize the string.
        This is enriched with additional transformation for parentesis.
        The basic normalized function can be found here
        https://github.com/OSGeo/gdal/blob/0fc262675051b63f96c91ca920d27503655dfb7b/ogr/ogrsf_frmts/pgdump/ogrpgdumpdatasource.cpp#L130  # noqa

        We use replace because it looks to be one of the fasted options:
        https://stackoverflow.com/questions/3411771/best-way-to-replace-multiple-characters-in-a-string
        """
        return (
            name.lower()
            .replace("-", "_")
            .replace(" ", "_")
            .replace("#", "_")
            .replace("\\", "_")
            .replace(".", "")
            .replace(")", "")
            .replace("(", "")
            .replace(",", "")
            .replace("&", "")[:62]
        )

    def extract_resource_to_publish(self, files, layer_name, alternate, **kwargs):
        """
        Function to extract the layer name and the CRS from needed in the
        publishing phase
        [
            {'name': 'alternate or layer_name', 'crs': 'EPSG:25832'}
        ]
        """
        return NotImplementedError

    def overwrite_geoserver_resource(self, resource, catalog, store, workspace):
        """
        Base method for override the geoserver resource. For vector file usually
        is not needed since the value are replaced by ogr2ogr
        """
        pass

    @staticmethod
    def create_error_log(exc, task_name, *args):
        """
        This function will handle the creation of the log error for each message.
        This is helpful and needed, so each handler can specify the log as needed
        """
        return f"Task: {task_name} raised an error during actions for layer: {args[-1]}: {exc}"

    def prepare_import(self, files, execution_id, **kwargs):
        """
        Optional preparation step to before the actual import begins.
        By default this does nothing.
        """
        pass

    def import_resource(self, files: dict, execution_id: str, **kwargs):
        """
        Define the step to perform the import of the data
        into the datastore db
        """
        return NotImplementedError

    @staticmethod
    def publish_resources(resources: List[str], catalog, store, workspace):
        """
        Given a list of strings (which rappresent the table on geoserver)
        Will publish the resorces on geoserver
        """
        return NotImplementedError

    def create_geonode_resource(self, layer_name, alternate, execution_id, resource_type: Dataset = Dataset):
        """
        Base function to create the resource into geonode. Each handler can specify
        and handle the resource in a different way
        """
        return NotImplementedError

    def create_resourcehandlerinfo(self, handler_module_path, resource, **kwargs):
        return NotImplementedError

    def get_ogr2ogr_task_group(self, execution_id, files, layer, should_be_overwritten, alternate):
        """
        implement custom ogr2ogr task group
        """
        return NotImplementedError

    def delete_resource(self, instance):
        """
        Base function to delete the resource with all the dependencies (example: dynamic model)
        """
        return NotImplementedError
