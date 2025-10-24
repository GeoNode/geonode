import logging

from django.db.models import Func, Value
from django.conf import settings

from geonode.base.models import ResourceBase
from geonode.indexing.models import ResourceIndex
import geonode.metadata.multilang as multi

logger = logging.getLogger(__name__)


class IndexManager:

    def __init__(self):
        self.LANGUAGES = multi.get_2letters_languages()

    def _gather_fields_values(self, jsonschema: dict, jsoninstance: dict):
        ml_fields = {}
        nonml_fields = {}

        involved_fields = {field for fields in settings.METADATA_INDEXES.values() for field in fields}

        # first loop: gather values
        for fieldname in involved_fields:
            if multi.is_multilang(fieldname, jsonschema):
                ml_fields[fieldname] = {}
                for lang, loc_field_name in multi.get_multilang_field_names(fieldname):
                    ml_fields[fieldname][lang] = jsoninstance.get(loc_field_name, "")
            else:
                nonml_fields[fieldname] = jsoninstance.get(fieldname, None)

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

        return nonml_fields, ml_fields

    def update_index(self, resource: ResourceBase, jsonschema: dict, jsoninstance: dict):

        nonml_fields, ml_fields = self._gather_fields_values(jsonschema, jsoninstance)

        # 3rd loop: create indexes
        for index_name, index_fields in settings.METADATA_INDEXES.items():

            if all(field in nonml_fields for field in index_fields):
                # this index is not localized
                pg_lang = multi.get_pg_language(multi.get_default_language())
                logger.debug(
                    f"Creating non localized index - resource:{resource.id} index name:{index_name} default lang:{pg_lang}"
                )
                index_text = " ".join((nonml_fields[f] for f in index_fields))
                vector = Func(
                    Value(index_text), function="to_tsvector", template=f"%(function)s('{pg_lang}', %(expressions)s)"
                )

                ResourceIndex.objects.update_or_create(
                    defaults={"vector": vector}, resource=resource, lang=None, name=index_name
                )
                # remove all localized indexes if any
                ResourceIndex.objects.filter(
                    resource=resource,
                    lang__isnull=False,
                    name=index_name,
                ).delete()

            else:  # some indexed fields are multilang
                # gather all non localized fields
                non_multilang_text = " ".join((nonml_fields[f] for f in index_fields))
                indexes = {}

                # compose indexes for each language
                for index_field in index_fields:
                    if index_field not in ml_fields:
                        continue
                    for lang, text in ml_fields[index_field]:
                        old = indexes.setdefault(lang, "")
                        indexes[lang] = f"{old} {text}"

                # store indexes for each language
                for lang, text in indexes.items():
                    logger.debug(f"Creating localized index {index_name} for resource {resource.id}")

                    pg_lang = multi.get_pg_language(lang)
                    vector = Func(
                        Value(f"{text} {non_multilang_text}"),
                        function="to_tsvector",
                        template=f"%(function)s('{pg_lang}', %(expressions)s)",
                    )

                    ResourceIndex.objects.update_or_create(
                        resource=resource, lang=lang, name=index_name, defaults={"vector": vector}
                    )

                # remove all non-localized indexes entries
                ResourceIndex.objects.filter(
                    resource=resource,
                    lang__isnull=True,
                    name=index_name,
                ).delete()


index_manager = IndexManager()
