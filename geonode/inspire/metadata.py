import logging
from rest_framework.reverse import reverse

from django.db.models import Q
from django.utils.translation import gettext as _

from geonode.base.models import ResourceBase, RestrictionCodeType, ThesaurusKeywordLabel
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.handlers.sparse import sparse_field_registry
from geonode.metadata.manager import metadata_manager
from geonode.metadata.handlers.thesaurus import TKeywordsHandler
from geonode.metadata.models import SparseField

logger = logging.getLogger(__name__)


FIELD_RESTRICTION_TYPE = "restriction_code_type"
FIELD_RESTRICTION_PUBLIC_ACCESS = "constraints_other"
FIELD_RESTRICTION_ACCESS_USE = "access_and_use"

THESAURUS_PUBLIC_ACCESS = "limitationsonpublicaccess"
THESAURUS_ACCESS_USE = "conditionsapplyingtoaccessanduse"

FIELDVAL_ACCESS_USE_FREETEXT = "http://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/freeText"
# Should be "otherRestrictions", see https://github.com/GeoNode/geonode/issues/12745
FIELDVAL_RESTRICTION_TYPE_DEFAULT = "limitation not listed"

CONTEXT_ID = "inspire"


class INSPIREHandler(MetadataHandler):
    """
    The INSPIRE Handler adds the Regions model options to the schema
    """

    def update_schema(self, jsonschema, context, lang=None):
        # Schema overriding for INSPIRE
        # Some Additional Sparse Fields are registered in geonode.inspire.inspire.init()

        # lineage is mandatory
        for prop in (
            "language",  # 2.2.2 TG Rq C.5
            "data_quality_statement",
        ):
            jsonschema["properties"][prop].update(
                {
                    "type": "string",  # exclude null
                    "geonode:required": True,
                }
            )

        # override base schema: was a codelist, is a fixed value in the codelist
        jsonschema["properties"][FIELD_RESTRICTION_TYPE] = {
            "type": "string",
            "title": "restrictions",
            "ui:widget": "hidden",
            "geonode:handler": "inspire",
        }

        collected_thesauri = TKeywordsHandler.collect_thesauri(
            Q(identifier__in=(THESAURUS_ACCESS_USE, THESAURUS_PUBLIC_ACCESS)), lang=lang
        )
        if THESAURUS_PUBLIC_ACCESS in collected_thesauri:
            ct = collected_thesauri[THESAURUS_PUBLIC_ACCESS]
            # override base schema: was free text, is an entry from a thesaurus
            jsonschema["properties"][FIELD_RESTRICTION_PUBLIC_ACCESS] = {
                "type": "object",
                "title": ct["title"],
                "description": ct["description"],
                "properties": {
                    "id": {
                        "type": "string",
                        "title": "keyword id",
                    },
                    "label": {
                        "type": "string",
                        "title": "Label",
                    },
                },
                "ui:options": {
                    "geonode-ui:autocomplete": reverse(
                        "metadata_autocomplete_tkeywords", kwargs={"thesaurusid": ct["id"]}
                    )
                },
                "geonode:handler": "inspire",
            }
        else:
            logger.warning(f"Missing thesaurus {THESAURUS_PUBLIC_ACCESS}")
            jsonschema["properties"][FIELD_RESTRICTION_PUBLIC_ACCESS] = {
                "type": "string",
                "title": _("Limitations on public access"),
                "readOnly": True,
                "geonode:handler": "inspire",
            }

        # As per §2.3.7 the conditions to access and use may be either:
        #  - a URI to indicate "noConditionsApply"
        #  - a URI to indicate  "conditionsUnknown"
        #  - a free text with a textual description of the condition
        # The standard thesaurus include only the first two options.
        # This implementation foresee:
        # - a dropdown to choose one of the 2 official entries and a custom added entry "http://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/freeText"
        # - a textarea for the free text
        # The textarea can be populated only if the freetext entry is selected, or there will be an error returned
        # by the server
        # Future implementations may refine the jsonschema to enable the textarea only when the freetext entry is selected

        if THESAURUS_ACCESS_USE in collected_thesauri:
            ct = collected_thesauri[THESAURUS_ACCESS_USE]
            access_use_subschema = {
                "type": "object",
                "title": ct["title"],
                "description": ct["description"],
                "properties": {
                    "choice": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "title": "keyword id",
                            },
                            "label": {
                                "type": "string",
                                "title": "Label",
                            },
                        },
                        "ui:options": {
                            "label": False,
                            "geonode-ui:autocomplete": reverse(
                                "metadata_autocomplete_tkeywords", kwargs={"thesaurusid": ct["id"]}
                            ),
                        },
                    },
                    "freetext": {
                        "title": "Conditions description",
                        "description": "Description of terms and conditions for access and use",
                        "type": ["string", "null"],
                        "ui:options": {
                            "widget": "textarea",
                            "rows": 3,
                            # "label": False,
                        },
                    },
                },
                "geonode:handler": "inspire",
            }

        else:
            logger.warning(f"Missing thesaurus {THESAURUS_ACCESS_USE}")
            access_use_subschema = {
                "type": "string",
                "title": _("Conditions applying to access and use"),
                "readOnly": True,
                "geonode:handler": "inspire",
            }

        self._add_after(jsonschema, FIELD_RESTRICTION_PUBLIC_ACCESS, FIELD_RESTRICTION_ACCESS_USE, access_use_subschema)

        return jsonschema

    def load_serialization_context(self, resource: ResourceBase, jsonschema: dict, context: dict):
        context[CONTEXT_ID] = {"schema": jsonschema}
        fields = {}
        for field in SparseField.get_fields(resource, names=(FIELD_RESTRICTION_ACCESS_USE,)):
            fields[field.name] = field.value
        context[CONTEXT_ID]["fields"] = fields

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        if field_name == FIELD_RESTRICTION_TYPE:
            # 1) as per TG Req C.17, fixed to "otherRestrictions"
            # 2) should be "otherRestrictions", see https://github.com/GeoNode/geonode/issues/12745
            return FIELDVAL_RESTRICTION_TYPE_DEFAULT

        elif field_name == FIELD_RESTRICTION_PUBLIC_ACCESS:
            if context[CONTEXT_ID]["schema"]["properties"][FIELD_RESTRICTION_PUBLIC_ACCESS].get("readOnly", False):
                self._set_error(
                    errors,
                    [FIELD_RESTRICTION_PUBLIC_ACCESS],
                    f"Missing thesaurus {THESAURUS_PUBLIC_ACCESS}. Please contact your administrator.",
                )
                return (
                    f"Missing Thesaurus {THESAURUS_PUBLIC_ACCESS}.\n"
                    "Get it from https://inspire.ec.europa.eu/metadata-codelist/LimitationsOnPublicAccess"
                )
            else:
                return {"id": resource.constraints_other}

        elif field_name == FIELD_RESTRICTION_ACCESS_USE:
            if context[CONTEXT_ID]["schema"]["properties"][FIELD_RESTRICTION_ACCESS_USE].get("readOnly", False):
                self._set_error(
                    errors,
                    [FIELD_RESTRICTION_ACCESS_USE],
                    f"Missing thesaurus {THESAURUS_ACCESS_USE}. Please contact your administrator.",
                )
                return (
                    f"Missing Thesaurus {THESAURUS_ACCESS_USE}.\n"
                    "Get it from https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse"
                )
            else:
                val = context[CONTEXT_ID]["fields"].get(FIELD_RESTRICTION_ACCESS_USE, None)
                if not val:
                    return {"choice": {"id": None}, "freetext": None}
                elif val.startswith("http"):
                    label = (
                        ThesaurusKeywordLabel.objects.filter(keyword__about=val, lang=lang)
                        .values_list("label", flat=True)
                        .first()
                    )
                    label = label or val.split("/")[-1]
                    return {"choice": {"id": val, "label": label}, "freetext": None}
                else:
                    return {"choice": {"id": FIELDVAL_ACCESS_USE_FREETEXT}, "freetext": val}

        else:
            raise Exception(f"The INSPIRE handler does not support field {field_name}")

    def load_deserialization_context(self, resource: ResourceBase, jsonschema: dict, context: dict):
        context[CONTEXT_ID] = {"schema": jsonschema}

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        if field_name == FIELD_RESTRICTION_TYPE:
            # 1) as per TG Req C.17, fixed to "otherRestrictions"
            resource.restriction_code_type = RestrictionCodeType.objects.filter(
                identifier=FIELDVAL_RESTRICTION_TYPE_DEFAULT
            ).first()
            if not resource.restriction_code_type:
                logger.warning(f"Default value '{FIELDVAL_RESTRICTION_TYPE_DEFAULT}' not found.")
                self._set_error(
                    errors,
                    [FIELD_RESTRICTION_TYPE],
                    f"Default value '{FIELDVAL_RESTRICTION_TYPE_DEFAULT}' not found. Please contact your administrator.",
                )

        elif field_name == FIELD_RESTRICTION_PUBLIC_ACCESS:
            field_value = json_instance.get(field_name, None)
            # This field contains a URI from a controlled vocabulary
            # TODO: validate against allowed values
            resource.constraints_other = field_value

        elif field_name == FIELD_RESTRICTION_ACCESS_USE:
            # This field contains either a URI from a controlled voc or a free text.
            # The schema contains a dropdown property (id+label) where the id is a URI from a controlled voc,
            # and a string object for the freetext.
            # We want the free text only if the choice contain the freetext related URI

            field_value = json_instance.get(field_name, {})

            if context[CONTEXT_ID]["schema"]["properties"][FIELD_RESTRICTION_ACCESS_USE].get("readOnly", False):
                content = "N/A"
                self._set_error(
                    errors,
                    [FIELD_RESTRICTION_ACCESS_USE],
                    f"Missing thesaurus {THESAURUS_ACCESS_USE}. Please contact your administrator.",
                )
            else:
                logger.debug(f"ACCESS AND USE --> {field_value}")
                uri = field_value["choice"]["id"]
                freetext = field_value.get("freetext", None)
                content = None
                if uri != FIELDVAL_ACCESS_USE_FREETEXT:
                    if freetext:
                        # save the text anyway, it may be hard to type it again
                        content = freetext
                        self._set_error(
                            errors,
                            [FIELD_RESTRICTION_ACCESS_USE],
                            "Textual content only allowed when freetext option is selected",
                        )
                    else:
                        content = uri
                else:
                    content = freetext
                    if not freetext:
                        self._set_error(errors, [FIELD_RESTRICTION_ACCESS_USE], "Textual content can't be empty")
            try:
                SparseField.objects.update_or_create(defaults={"value": content}, resource=resource, name=field_name)
            except Exception as e:
                logger.warning(f"Error setting field {field_name}={field_value}: {e}")
                self._set_error(errors, ["field_name"], f"Error setting value: {e}")
        else:
            raise Exception(f"The INSPIRE handler does not support field {field_name}")


def init():
    logger.info("Initting INSPIRE hooks")
    # == Add json schema

    # TG Requirement 1.5: metadata/2.0/req/datasets-and-series/spatial-resolution
    schema_res = {
        "type": "number",
        "title": "res_distance",
        "description": "Level of detail of the data set in metres",
    }
    sparse_field_registry.register("accuracy", schema_res, after="spatial_representation_type")

    metadata_manager.add_handler("inspire", INSPIREHandler)

    # TODO: register metadata parser

    # TODO: register metadata storer

    # TODO: set metadata template

    # TODO: check for mandatory thesauri

    # TODO: reload schema on thesaurus+thesauruskeywords signal
