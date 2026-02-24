import logging

from django.conf import settings
from rest_framework import serializers

from geonode.metadata.multilang import utils as multi


logger = logging.getLogger(__name__)


class MultiLangOutputMixin(serializers.BaseSerializer):

    def to_representation(self, instance):

        representation = super().to_representation(instance)
        request = self.context.get("request")
        params = getattr(request, "query_params", None) or getattr(request, "GET", {})
        include_i18n = params.get("include_i18n", "false").lower() == "true" if request else False
        target_lang = multi.get_language(request)

        if settings.MULTILANG_FIELDS and hasattr(instance, "_multilang_sparse_prefetch"):
            multilang_field_map = multi.get_all_multilang_fields()

            sparse_value_map = {sparse.name: sparse.value for sparse in instance._multilang_sparse_prefetch}

            for (base_field_name, lang_code), sparse_field_name in multilang_field_map.items():

                if sparse_field_name not in sparse_value_map:
                    continue

                value = sparse_value_map[sparse_field_name]

                if lang_code == target_lang:
                    representation[base_field_name] = value

                if include_i18n:
                    representation[f"{base_field_name}_{lang_code}"] = value

        return representation
