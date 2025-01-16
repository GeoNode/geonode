import logging

from django.db import connection

logger = logging.getLogger(__name__)

I18N_THESAURUS_IDENTIFIER = "labels-i18n"


def get_localized_tkeywords(lang, thesaurus_identifier: str):
    logger.debug(f"Loading localized tkeyword from DB lang:{lang}")

    query = (
        "select "
        "	tk.id,"
        "	tk.about,"
        "	tk.alt_label,"
        "	tkl.label"
        " from"
        "	base_thesaurus th,"
        "   base_thesauruskeyword tk"
        " left outer join "
        "  (select keyword_id, lang, label from base_thesauruskeywordlabel"
        "   where lang = %s) as tkl"
        " on (tk.id = tkl.keyword_id)"
        " where th.identifier = %s"
        " and tk.thesaurus_id = th.id"
        " order by label, alt_label"
    )
    ret = []
    with connection.cursor() as cursor:
        cursor.execute(query, [lang, thesaurus_identifier])
        for id, about, alt, label in cursor.fetchall():
            ret.append({"id": id, "about": about, "label": label or alt})
    return sorted(ret, key=lambda i: i["label"].lower())


def get_localized_labels(lang, key="about"):
    return {i[key]: i["label"] for i in get_localized_tkeywords(lang, I18N_THESAURUS_IDENTIFIER)}
