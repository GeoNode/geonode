import logging

from django.conf import settings
from rest_framework import serializers


logger = logging.getLogger(__name__)


class MultiLangOutputMixin(serializers.BaseSerializer):

    def to_representation(self, instance):

        representation = super().to_representation(instance)

        if settings.MULTILANG_FIELDS and hasattr(instance, "_multilang_sparse_prefetch"):
            for sparse in instance._multilang_sparse_prefetch:
                base_field_name = sparse.name[:-13]  # name_multilang_xx
                if base_field_name in representation:
                    logger.debug(f"setting into {instance} field {base_field_name} --> {sparse.value}")
                    representation[base_field_name] = sparse.value

        return representation
