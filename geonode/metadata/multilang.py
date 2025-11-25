from django.conf import settings


def get_2letters_languages():
    return [lang.split("-")[0] for lang, _ in settings.LANGUAGES]


def get_multilang_field_names(base_name):
    return ((lang, f"{base_name}_multilang_{lang}") for lang in get_2letters_languages())


def get_pg_language(lang):
    return settings.MULTILANG_POSTGRES_LANGS.get(lang, None) or settings.MULTILANG_POSTGRES_LANGS.get(None)


def get_default_language():
    return settings.LANGUAGE_CODE
