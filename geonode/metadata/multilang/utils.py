from django.conf import settings


def get_2letters_languages():
    """
    Return the list of languages in settings.LANGUAGES
    with the default language as first element
    """
    langs = [lang.split("-")[0] for lang, _ in settings.LANGUAGES]
    i = langs.index(settings.LANGUAGE_CODE)
    if i != 0:
        langs.pop(i)
        langs.insert(0, settings.LANGUAGE_CODE)
    return langs


def get_multilang_field_names(base_name):
    return ((lang, get_multilang_field_name(base_name, lang)) for lang in get_2letters_languages())


def get_multilang_fields_for_lang(lang):
    return [get_multilang_field_name(field_name, lang) for field_name in settings.MULTILANG_FIELDS]


def get_multilang_field_name(base_name, lang):
    return f"{base_name}_multilang_{lang}"


def get_pg_language(lang):
    return settings.MULTILANG_POSTGRES_LANGS.get(lang, None) or settings.MULTILANG_POSTGRES_LANGS.get(None)


def get_default_language():
    return settings.LANGUAGE_CODE


def get_language(request):
    if request:
        params = getattr(request, "query_params", None) or getattr(request, "GET", {})
        language = params.get("lang", None)

        if not language:
            language = getattr(request, "LANGUAGE_CODE", None)  # LocaleMiddleware
        if not language:
            headers = getattr(request, "headers", {})
            language = headers.get("Accept-Language", "").split(",")[0]
    else:
        language = get_default_language()

    if language and "-" in language:
        language = language.split("-")[0]  # normalize

    return language


def get_all_multilang_fields():
    return {
        (field, lang): get_multilang_field_name(field, lang)
        for field in settings.MULTILANG_FIELDS
        for lang in get_2letters_languages()
    }


def get_3_from_2(lang_2):
    """
    Return the preferred ISO 639-2 (3-letter) code for an ISO 639-1 code.
    """
    mappings = getattr(settings, "LANGUAGE_MAPPINGS", ())
    if not isinstance(mappings, dict):
        mappings = dict(mappings)

    code = mappings.get(lang_2)
    if isinstance(code, (list, tuple)):
        return code[0] if code else None
    return code


def get_2_from_3(lang_3):
    """
    Return the ISO 639-1 (2-letter) code for a given ISO 639-2 (3-letter) code.
    """
    mappings = getattr(settings, "LANGUAGE_MAPPINGS", ())
    if isinstance(mappings, dict):
        mappings = mappings.items()

    for lang_2, lang_3_codes in mappings:
        codes = lang_3_codes if isinstance(lang_3_codes, (list, tuple)) else (lang_3_codes,)
        if lang_3 in codes:
            return lang_2
    return None
