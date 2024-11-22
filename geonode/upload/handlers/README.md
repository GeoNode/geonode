# Hanlder Definition

As handler we define an object which is able to import a specific new resource in GeoNode.

The main base code of each handler is defined under the `common` structure.
The `common` structure is meant to define the common step needed for each handler.

For example for the `vector` file type, almost all the steps are in common.

# How to create a new handler

A new handler MUST implement the following function to make it works with the actual architecture.

Follows a default handler structure complain with the importer architecture

```python
import logging
from typing import List

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.layers.models import Dataset
from geonode.upload.handlers.base import BaseHandler
from geonode.resource.models import ExecutionRequest

logger = logging.getLogger("importer")



class BaseVectorFileHandler(BaseHandler):
    """
    Handler to import Vector files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """
    
    TASKS = {
        exa.IMPORT.value: (),  # define the list of the step (celery task) needed to execute the action for the resource
        exa.COPY.value: (),
        exa.DELETE.value: (),
        exa.UPDATE.value: (),
    }

    @property
    def supported_file_extension_config(self):
        '''
        Return the JSON configuration for the FE
        needed to enable the new handler in the UI
        '''
        return {
            "id": "id",
            "label": "label",
            "format": "metadata",
            "ext": ["ext"],
            "optional": ["xml", "sld"],
        }


    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Used in the import_resource step. It defines if the processed resource
        can be considered valid or not. If not in the import_resource step
        an exeption is raised
        """
        return True

    @staticmethod
    def can_handle(_data) -> bool:
        """
        Used in the upload API.
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        return True

    @staticmethod
    def has_serializer(_data) -> bool:
        '''
        Used in the upload API.        
        This endpoint will return False if no custom serializer are defined, otherwise
        it should return the serializer needed to validate the input API
        Check the shapefile handler for more info
        '''
        return False

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        return

    @staticmethod
    def publish_resources(resources: List[str], catalog, store, workspace):
        """
        Given a list of strings (which rappresent the table name)
        Will publish the resorces on geoserver
        """
        return

    @staticmethod
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate):
        """
        Define the ogr2ogr command to be executed.
        This is a default command that is needed to import a vector file. For Raster file
        this function is not needed
        """
        return

    @staticmethod
    def delete_resource(instance):
        """
        Base function to delete the resource with all the dependencies (example: dynamic model)
        """
        return

    @staticmethod
    def perform_last_step(execution_id):
        '''
        Override this method if there is some extra step to perform
        before considering the execution as completed.
        For example can be used to trigger an email-send to notify
        that the execution is completed
        '''
        return

    def extract_resource_to_publish(self, files, action, layer_name, alternate, **kwargs):
        """
        Function to extract the layer name and the CRS from needed in the
        publishing phase
        [
            {'name': 'alternate or layer_name', 'crs': 'EPSG:25832'}
        ]
        """
        return

    def get_ogr2ogr_driver(self):
        """
        Should return the Driver object that is used to open the layers via OGR2OGR
        """
        return None

    def import_resource(self, files: dict, execution_id: str, **kwargs) -> str:
        """
        Main function to import the resource.
        Internally will call the steps required to import the
        data inside the geonode_data database
        """
        return

    def create_geonode_resource(
        self, layer_name: str, alternate: str, execution_id: str, resource_type: Dataset = Dataset, files=None
    ):
        """
        Base function to create the resource into geonode. Each handler can specify
        and handle the resource in a different way. Is highly suggested to use
        the GeoNode resource_manager
        """
        return

    def overwrite_geonode_resource(
        self, layer_name: str, alternate: str, execution_id: str, resource_type: Dataset = Dataset, asset=None
    ):
        """
        Base function to override the resource into geonode. Each handler can specify
        and handle the resource in a different way. Is highly suggested to use
        the GeoNode resource_manager
        """
        return

    def handle_xml_file(self, saved_dataset: Dataset, _exec: ExecutionRequest):
        """
        Base function to import the XML within the resource. Each handler can specify
        and handle the resource in a different way. Is highly suggested to use
        the GeoNode resource_manager
        """
        return

    def handle_sld_file(self, saved_dataset: Dataset, _exec: ExecutionRequest):
        """
        Base function to import the SLD within the resource. Each handler can specify
        and handle the resource in a different way. Is highly suggested to use
        the GeoNode resource_manager
        """
        return

    def create_resourcehandlerinfo(self, handler_module_path: str, resource: Dataset, execution_id: ExecutionRequest, **kwargs):
        """
        Create relation between the GeonodeResource and the handler used
        to create/copy it
        """
        return

    def overwrite_resourcehandlerinfo(self, handler_module_path: str, resource: Dataset, execution_id: ExecutionRequest, **kwargs):
        """
        Overwrite the ResourceHandlerInfo
        """
        return

    def copy_geonode_resource(
        self, alternate: str, resource: Dataset, _exec: ExecutionRequest, data_to_update: dict, new_alternate: str, **kwargs
    ):
        """
        Base function to copy already exists Geonode Resource. Each handler can specify
        and handle the resource in a different way. Is highly suggested to use
        the GeoNode resource_manager
        """
        return

```

### Additional info

- `ACTION`: this property represents the list of the action (import/copy/etc..) that the handler can perform. Each `ACTION` must define the list of the celery task (steps) that the orchestrator must call to successfully import/copy/etc.. the resource.

- `supported_file_extension_config`: Need to let show the new supported type in the front-end


# Using a common structure:

Not all handlers must redefine the above structure. If the resource type is a `vector` file, the `common` file can be used to have a structure already in place, for example:

```python
import logging

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.api.exceptions import UploadParallelismLimitException
from geonode.upload.utils import UploadLimitValidator
from geopackage_validator.validate import validate
from geonode.upload.handlers.gpkg.exceptions import InvalidGeopackageException
from osgeo import ogr

from geonode.upload.handlers.common.vector import BaseVectorFileHandler

logger = logging.getLogger("importer")



class NewVectorFileHandler(BaseVectorFileHandler):
    """
    Handler to import GPK files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    TASKS = {
        exa.IMPORT.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        ),
        exa.COPY.value: (
            "start_copy",
            "geonode.upload.copy_dynamic_model",
            "geonode.upload.copy_geonode_data_table",
            "geonode.upload.publish_resource",
            "geonode.upload.copy_geonode_resource",
        ),
    }

    @property
    def supported_file_extension_config(self):
        return {"id": "gpkg", "label": "GeoPackage", "format": "archive", "ext": ["gpkg"]}

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        return

    @staticmethod
    def is_valid(files, user, **kwargs):
        return True

    def get_ogr2ogr_driver(self):
        return ogr.GetDriverByName("GPKG")

```


# How to register the new handler

Once the new handler is defined, it must be registered in the settings like a Django application:

```
IMPORTER_HANDLERS = os.getenv('IMPORTER_HANDLERS', [
    'geonode.upload.handlers.gpkg.handler.GPKGFileHandler',
    'path.to.my.new.Handler.' <----
])
```