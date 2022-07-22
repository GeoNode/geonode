
import enum
from django.utils.translation import gettext_lazy as _


class ExecutionRequestAction(enum.Enum):
    upload = _("upload")  # import will be better, but it will clash with the python import statement
    create = _("create")
    copy = _("copy")
    delete = _("delete")
    permissions = _("permissions")
    update = _("update")
    ingest = _("ingest")
    unknown = _("unknown")
