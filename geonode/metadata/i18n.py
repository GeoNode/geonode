import logging

from django.db import connection

from geonode.base.models import ThesaurusKeywordLabel

logger = logging.getLogger(__name__)

I18N_THESAURUS_IDENTIFIER = "labels-i18n"


def get_localized_tkeywords(lang, thesaurus_identifier: str):
    logger.debug(f"Loading localized tkeyword from DB lang:{lang}")

    query = (
        "select "
        "	tk.id,"
        "	tk.about,"
        "	tk.alt_label,"
        "	tkl.label,"
        "	tkl.lang"
        " from"
        "	base_thesaurus th,"
        "   base_thesauruskeyword tk"
        " left outer join "
        "  (select keyword_id, lang, label from base_thesauruskeywordlabel"
        "   where lang like %s) as tkl"
        " on (tk.id = tkl.keyword_id)"
        " where th.identifier = %s"
        " and tk.thesaurus_id = th.id"
        " order by label, alt_label"
    )
    ret = {}
    ovr = {}
    with connection.cursor() as cursor:
        cursor.execute(query, [f"{lang}%", thesaurus_identifier])
        for id, about, alt, label, dblang in cursor.fetchall():
            if not dblang or dblang == lang:
                # this is a properly localized label or an altlabel (when dblang is null)
                ret[id] = {"id": id, "about": about, "label": label or alt}
            elif dblang and dblang.endswith("-ovr"):
                # store overrides to be applied later
                ovr[id] = {"id": id, "about": about, "label": label or alt}
            else:
                logger.warning(f"Found unexpected lang {dblang}")
        for ovr_id, ovr_row in ovr.items():  # apply overrides
            if ovr_id in ret:
                logger.debug(f"overriding TK {ret[ovr_id]['about']}")
                ret[ovr_id]["label"] = ovr_row["label"]
            else:
                logger.debug(f"Setting ovr TK {ovr_row}")
                ret[ovr_id] = ovr_row

    return sorted(ret.values(), key=lambda i: i["label"].lower())


def get_localized_labels(lang, key="about"):
    return {i[key]: i["label"] for i in get_localized_tkeywords(lang, I18N_THESAURUS_IDENTIFIER)}


def get_localized_label(lang, about):
    return (
        ThesaurusKeywordLabel.objects.filter(
            keyword__thesaurus__identifier=I18N_THESAURUS_IDENTIFIER, keyword__about=about, lang=lang
        )
        .values_list("label", flat=True)
        .first()
    )
