import logging

from django.conf import settings
from rest_framework import serializers
from geonode.metadata.multilang import utils as multi


logger = logging.getLogger(__name__)


class MultiLangOutputMixin(serializers.BaseSerializer):

    def to_representation(self, instance):

        representation = super().to_representation(instance)
        request = self.context.get('request')
        include_i18n = request.query_params.get('include_i18n', 'false').lower() == 'true' if request else False

        if settings.MULTILANG_FIELDS and hasattr(instance, "_multilang_sparse_prefetch"):
            for sparse in instance._multilang_sparse_prefetch:
                base_field_name = sparse.name[:-13]  # name_multilang_xx
                lang_code = sparse.name[-2:]

                if base_field_name in representation:
                    if not include_i18n:
                        representation[base_field_name] = sparse.value
                    else:
                        if lang_code == multi.get_language(request):
                            representation[base_field_name] = sparse.value
                        representation[f"{base_field_name}_{lang_code}"] = sparse.value

        return representation
