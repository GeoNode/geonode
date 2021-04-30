from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.utils.translation import get_language
from geonode.base.models import Thesaurus, ThesaurusKeywordLabel, ThesaurusLabel

register = template.Library()


@register.filter
def get_unique_thesaurus_set(thesaurus_from_keyword):
    return set(thesaurus_from_keyword.values_list("thesaurus", flat=True))


@register.filter
def get_thesaurus_title(thesaurus_id):
    return Thesaurus.objects.get(id=thesaurus_id).title


@register.filter
def get_thesaurus_date(thesaurus_id):
    return Thesaurus.objects.get(id=thesaurus_id).date


@register.filter
def get_name_translation(tidentifier):
    lang = get_language()
    available = Thesaurus.objects.filter(identifier=tidentifier)
    if not available.exists():
        raise ObjectDoesNotExist("Selected idenfifier does not exists")
    lname = (
        ThesaurusLabel.objects.values_list("label", flat=True)
        .filter(thesaurus__identifier=tidentifier)
        .filter(lang=lang)
    )
    if not lname:
        return available.first().title
    return lname.first()


@register.filter
def get_thesaurus_translation_by_id(id):
    available = Thesaurus.objects.filter(id=id)
    if not available.exists():
        raise ObjectDoesNotExist("Selected idenfifier does not exists")
    return get_name_translation(available.first().identifier)


@register.filter
def get_thesaurus_localized_label(tkeyword):
    lang = get_language()
    translation = (
        ThesaurusKeywordLabel.objects.values_list("label", flat=True)
        .filter(keyword__id=tkeyword.id)
        .filter(lang=lang)
    )
    if not translation:
        return tkeyword.alt_label
    return translation.first()
