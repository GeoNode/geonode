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
    get_2letters_languages,
    get_default_language,
    get_3_from_2,
    get_2_from_3,
    get_multilang_field_name,
)

register = template.Library()
logger = logging.getLogger(__name__)


def _is_multilang_field(field_name):
    """Return whether a field is configured as multilingual."""
    return field_name in getattr(settings, "MULTILANG_FIELDS", ())


def _language_label(language_code_2, fallback):
    """
    Return the display label for a configured language.
    """
    language_labels = {code.split("-")[0]: label for code, label in settings.LANGUAGES}

    return language_labels.get(language_code_2, fallback)


def _translation_value(metadata, field_name, language_code):
    """Return the translated value for a multilingual field."""
    if not metadata:
        return None

    return metadata.get(get_multilang_field_name(field_name, language_code))


def _has_translation(metadata, field_name, language_code):
    """Return whether the field has a translation for the given language."""
    return bool(
        _translation_value(
            metadata,
            field_name,
            language_code,
        )
    )


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
    return _is_multilang_field(field_name)


@register.simple_tag(name="multilang_values")
def multilang_values(field_name, metadata):
    """
    Return all translations for a multilingual field except the default
    language.
    """
    if not metadata or not _is_multilang_field(field_name):
        return []

    default_language = get_default_language()
    translations = []

    for language_code in get_2letters_languages():
        if language_code == default_language:
            continue

        translated_text = _translation_value(
            metadata,
            field_name,
            language_code,
        )

        if translated_text:
            translations.append(
                {
                    "locale": language_code,
                    "text": translated_text,
                }
            )

    return translations


@register.simple_tag(name="language_info")
def language_info(lang_3):
    """
    Return information about a single ISO639-2 language.
    """
    lang_2 = get_2_from_3(lang_3)

    if lang_2 is None:
        logger.warning(
            "No ISO639-1 language found for '%s'; using the ISO639-2 code as the label.",
            lang_3,
        )

    return _language_descriptor(
        lang_2 or lang_3,
        lang_3,
    )


@register.simple_tag(name="languages_info")
def languages_info(metadata, fields=None):
    """
    Return descriptors for all translated languages present in the metadata.
    """
    if not metadata:
        return []

    multilingual_fields = fields if fields is not None else getattr(settings, "MULTILANG_FIELDS", ())

    default_language = get_default_language()
    descriptors = []

    for language_code in get_2letters_languages():
        if language_code == default_language:
            continue

        if not any(
            _has_translation(metadata, field_name, language_code)
            for field_name in multilingual_fields
            if _is_multilang_field(field_name)
        ):
            continue

        lang_3 = get_3_from_2(language_code)

        if lang_3 is None:
            logger.warning(
                "No entry in settings.LANGUAGE_MAPPINGS for language '%s'; " "skipping this entry.",
                language_code,
            )
            continue

        descriptors.append(
            _language_descriptor(
                language_code,
                lang_3,
            )
        )

    return descriptors
