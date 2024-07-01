import json
import logging
from django.db import models
from django.forms import widgets
from django.contrib import admin

from geonode.assets.local import LocalAssetHandler
from geonode.assets.models import LocalAsset
from geonode.base.models import Link

logger = logging.getLogger(__name__)


class PrettyJSONWidget(widgets.Textarea):

    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=2, sort_keys=True)
            # these lines will try to adjust size of TextArea to fit to content
            row_lengths = [len(r) for r in value.split("\n")]
            self.attrs["rows"] = min(max(len(row_lengths) + 2, 10), 30)
            self.attrs["cols"] = min(max(max(row_lengths) + 2, 40), 120)
            return value
        except Exception as e:
            logger.warning("Error while formatting JSON: {}".format(e))
            return super(PrettyJSONWidget, self).format_value(value)


@admin.register(LocalAsset)
class LocalAssetAdmin(admin.ModelAdmin):
    model = LocalAsset

    list_display = ("id", "title", "type", "owner", "created_formatted", "managed", "links", "link0")
    list_display_links = ("id", "title")

    formfield_overrides = {models.JSONField: {"widget": PrettyJSONWidget}}

    def created_formatted(self, obj):
        return obj.created.strftime("%Y-%m-%d %H:%M:%S")

    def links(self, obj):
        return Link.objects.filter(asset=obj).count()

    def link0(self, obj):
        link = Link.objects.filter(asset=obj).first()
        return f"{link.link_type} {link.extension}: {link.name}" if link else None

    def managed(self, obj) -> bool:
        try:
            return LocalAssetHandler._is_file_managed(obj.location[0])
        except Exception as e:
            logger.error(f"Bad location for asset obj: {e}")
            return None

    managed.boolean = True
