import logging

from django.db.models import Prefetch

from geonode.metadata.models import SparseField
from geonode.metadata.multilang import utils as multi


logger = logging.getLogger(__name__)


class MultiLangViewMixin:
    """
    View mixin to enrich the queryset of ResourceBase-like models
    by prefetching localized fields and attaching them dynamically.
    """

    def get_queryset(self):
        """Adds a Prefetch to include localized fields in one query."""
        lang = multi.get_language(getattr(self, "request", None))
        field_names = multi.get_multilang_fields_for_lang(lang)

        qs = super().get_queryset()

        if not field_names:
            return qs

        # Prefetch all localized rows for this language
        prefetch = Prefetch(
            "sparsefield_set",  # this must match related_name on FK
            queryset=SparseField.objects.filter(name__in=field_names),
            to_attr="_multilang_sparse_prefetch",
        )

        qs = qs.prefetch_related(prefetch)
        return qs
