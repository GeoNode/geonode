from django import template
from geonode.base.models import Thesaurus, ThesaurusKeywordLabel
from django.conf import settings

register = template.Library()


@register.filter
def get_unique_thesaurus_set(thesaurus_from_keyword):
    return set(thesaurus_from_keyword.values_list("thesaurus", flat=True))


@register.filter
def get_keyword_label(keyword):
    lang = "en" if not hasattr(settings, "THESAURUS_DEFAULT_LANG") else settings.THESAURUS_DEFAULT_LANG
    return ThesaurusKeywordLabel.objects.filter(keyword=keyword).filter(lang=lang).first().label


@register.filter
def get_thesaurus_title(thesaurus_id):
    return Thesaurus.objects.get(id=thesaurus_id).title


@register.filter
def get_thesaurus_date(thesaurus_id):
    return Thesaurus.objects.get(id=thesaurus_id).date
