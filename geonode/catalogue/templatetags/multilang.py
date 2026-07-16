#########################################################################
#
# Copyright (C) 2026 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import logging

from django import template
from django.conf import settings

from geonode.metadata.multilang.utils import (
    get_default_language,
    get_3_from_2,
    get_2_from_3,
    get_multilang_field_names,
    get_all_multilang_fields,
)

register = template.Library()
logger = logging.getLogger(__name__)


def _language_label(language_code_2, fallback):
    """
    Return the display label for a configured language.
    """
    language_labels = {code.split("-")[0]: label for code, label in settings.LANGUAGES}

    return language_labels.get(language_code_2, fallback)


def _language_descriptor(lang_2, lang_3):
    """Build the language descriptor used by the ISO template."""
    return {
        "id": f"locale-{lang_2}",
        "iso639_2": lang_3,
        "label": _language_label(lang_2, lang_3),
        "encoding": "utf8",
    }


@register.filter(name="is_multilang")
def is_multilang(field_name):
    """Return whether the field is configured as multilingual."""
    return field_name in getattr(settings, "MULTILANG_FIELDS", ())


@register.simple_tag(name="multilang_values")
def multilang_values(field_name, metadata):
    """
    Return all localized values for a multilingual field.
    """
    if not isinstance(metadata, dict) or not is_multilang(field_name):
        return []

    values = []

    for language_code, translated_field in get_multilang_field_names(field_name):
        translated_text = metadata.get(translated_field)
        if not translated_text:
            continue

        if get_3_from_2(language_code) is None:
            logger.warning(
                "No entry in LANGUAGE_MAPPINGS for language '%s'; " "skipping localized value for field '%s'.",
                language_code,
                field_name,
            )
            continue

        values.append(
            {
                "locale": language_code,
                "text": translated_text,
            }
        )

    return values


@register.simple_tag(name="language_info")
def language_info(lang_3):
    """
    Return information about a single ISO639-2 language.
    """
    if not lang_3:
        lang_2 = get_default_language()
        lang_3 = get_3_from_2(lang_2)
        if lang_3 is None:
            logger.warning(
                "No ISO639-2 language found for '%s'; using 'eng' as the default.",
                lang_2,
            )
            lang_3 = "und"
    elif len(lang_3) == 2:
        lang_2 = lang_3
        lang_3 = get_3_from_2(lang_2) or "und"
    else:
        lang_2 = get_2_from_3(lang_3)

        if lang_2 is None:
            logger.warning(
                "No ISO639-1 language found for '%s'; using the ISO639-2 code as the label.",
                lang_3,
            )

    return _language_descriptor(
        lang_2,
        lang_3,
    )


@register.simple_tag(name="languages_info")
def languages_info(metadata, fields=None):
    """
    Return descriptors for all translated languages present in the metadata.
    """
    if not isinstance(metadata, dict):
        return []

    multilingual_fields = set(fields or settings.MULTILANG_FIELDS)

    languages = set()

    for (field_name, language_code), multilang_field_name in get_all_multilang_fields().items():
        if field_name not in multilingual_fields or not metadata.get(multilang_field_name):
            continue

        languages.add(language_code)

    descriptors = []
    for language_code in sorted(languages):
        lang_3 = get_3_from_2(language_code)

        if lang_3 is None:
            logger.warning(
                "No entry in LANGUAGE_MAPPINGS for language '%s'; skipping this entry.",
                language_code,
            )
            continue

        descriptors.append(_language_descriptor(language_code, lang_3))

    return descriptors
