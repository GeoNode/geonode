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
        language = request.query_params.get("lang", None)  # explicit query param
        if not language:
            language = getattr(request, "LANGUAGE_CODE", None)  # LocaleMiddleware
        if not language:
            language = request.headers.get("Accept-Language", "").split(",")[0]
    else:
        language = get_default_language()

    if language and "-" in language:
        language = language.split("-")[0]  # normalize

    return language
