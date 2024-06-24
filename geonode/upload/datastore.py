from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model


class DataStoreManager:
    """
    Utility object to invoke the right handler used to save the
    resource in the datastore db
    """

    def __init__(
        self,
        files: list,
        handler_module_path: str,
        user: get_user_model(),  # type: ignore
        execution_id: str,
    ) -> None:
        self.files = files
        self.handler = import_string(handler_module_path)
        self.user = user
        self.execution_id = execution_id

    def input_is_valid(self):
        """
        Perform basic validation steps
        """
        return self.handler.is_valid(self.files, self.user)

    def prepare_import(self, **kwargs):
        """
        prepares the data before the actual import
        """
        return self.handler().prepare_import(self.files, self.execution_id, **kwargs)

    def start_import(self, execution_id, **kwargs):
        """
        call the resource handler object to perform the import phase
        """
        return self.handler().import_resource(self.files, execution_id, **kwargs)
