import logging

from django.db.models import Func, Value
from django.conf import settings

from geonode.indexing.models import ResourceIndex
import geonode.metadata.multilang.utils as multi

logger = logging.getLogger(__name__)


class TSVectorIndexManager:

    def __init__(self):
        self.LANGUAGES = multi.get_2letters_languages()

    def _gather_fields_values(self, jsoninstance: dict):
        ml_fields = {}
        non_ml_fields = {}

        involved_fields = {field for fields in settings.METADATA_INDEXES.values() for field in fields}

        # first loop: gather values
        for fieldname in involved_fields:
            if fieldname in settings.MULTILANG_FIELDS:
                ml_fields[fieldname] = {}
                for lang, loc_field_name in multi.get_multilang_field_names(fieldname):
                    ml_fields[fieldname][lang] = jsoninstance.get(loc_field_name, "")
            else:
                non_ml_fields[fieldname] = jsoninstance.get(fieldname, None)

        # 2nd loop: fill in missing title entries
        # i.e. if a title is missing the content for a given lang, it will be filled with the content
        # of every other lang to allow the entry to be discoverable.
        if "title" in involved_fields and "title" in ml_fields:
            if any(not content for content in ml_fields["title"].values()):
                merged = " ".join([content for content in ml_fields["title"].values() if content])
                merged = f"{merged} {jsoninstance.get('title', '')}"  # also add plain title

                for lang, content in ml_fields["title"].items():
                    if not content:
                        logger.debug(f"Filling in title for empty lang {lang}")
                        ml_fields["title"][lang] = merged

        return non_ml_fields, ml_fields

    def update_index(self, resource_id, jsoninstance: dict):

        non_ml_fields, ml_fields = self._gather_fields_values(jsoninstance)

        # 3rd loop: create indexes
        for index_name, index_fields in settings.METADATA_INDEXES.items():

            if all(field in non_ml_fields for field in index_fields):
                # this index is not localized
                pg_lang = multi.get_pg_language(multi.get_default_language())
                logger.debug(
                    f"Creating non localized index - resource:{resource_id} index name:{index_name} default lang:{pg_lang}"
                )
                index_text = " ".join(filter(None, (non_ml_fields[f] for f in index_fields)))
                vector = Func(
                    Value(index_text), function="to_tsvector", template=f"%(function)s('{pg_lang}', %(expressions)s)"
                )

                ResourceIndex.objects.update_or_create(
                    defaults={"vector": vector}, resource_id=resource_id, lang=None, name=index_name
                )
                # remove all localized indexes if any
                ResourceIndex.objects.filter(
                    resource_id=resource_id,
                    lang__isnull=False,
                    name=index_name,
                ).delete()

            else:  # some indexed fields are multilang
                # gather all non localized fields
                non_ml_text = " ".join(filter(None, (non_ml_fields[f] for f in index_fields if f in non_ml_fields)))

                for lang in self.LANGUAGES:
                    logger.debug(f"Creating localized index {index_name} for resource {resource_id}")

                    ml_text = " ".join(filter(None, (ml_fields[f][lang] for f in index_fields if f in ml_fields)))
                    vector = Func(
                        Value(" ".join(filter(None, [ml_text, non_ml_text]))),
                        function="to_tsvector",
                        template=f"%(function)s('{multi.get_pg_language(lang)}', %(expressions)s)",
                    )

                    ResourceIndex.objects.update_or_create(
                        resource_id=resource_id, lang=lang, name=index_name, defaults={"vector": vector}
                    )

                # remove all non-localized indexes entries
                ResourceIndex.objects.filter(
                    resource_id=resource_id,
                    lang__isnull=True,
                    name=index_name,
                ).delete()


index_manager = TSVectorIndexManager()
