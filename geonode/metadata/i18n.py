import logging
from datetime import datetime

from cachetools import FIFOCache
from django.db import connection

from geonode.base.models import ThesaurusKeywordLabel, Thesaurus


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


def get_localized_label(lang, about):
    return (
        ThesaurusKeywordLabel.objects.filter(
            keyword__thesaurus__identifier=I18N_THESAURUS_IDENTIFIER, keyword__about=about, lang=lang
        )
        .values_list("label", flat=True)
        .first()
    )


class I18nCache:

    DATA_KEY_SCHEMA = "schema"
    DATA_KEY_LABELS = "labels"

    def __init__(self):
        # the cache has the lang as key, and various info in the dict value:
        # - date: the date field of the thesaurus when it was last loaded, it's used for the expiration check
        # - labels: the keyword labels from the i18n thesaurus
        # - schema: the localized json schema
        # FIFO bc we want to renew the data once in a while
        self.cache = FIFOCache(16)

    def get_entry(self, lang, data_key):
        """
        returns date:str, data
        date is needed for checking the entry freshness when setting info
        data may be None if not cached or expired
        """
        cached_entry = self.cache.get(lang, None)

        thesaurus_date = (  # may be none if thesaurus does not exist
            Thesaurus.objects.filter(identifier=I18N_THESAURUS_IDENTIFIER).values_list("date", flat=True).first()
        )
        if cached_entry:
            if thesaurus_date == cached_entry["date"]:
                # only return cached data if thesaurus has not been modified
                return thesaurus_date, cached_entry.get(data_key, None)
            else:
                logger.info(f"Schema for {lang}:{data_key} needs to be recreated")

        return thesaurus_date, None

    def set(self, lang: str, data_key: str, data: dict, request_date: str):
        cached_entry: dict = self.cache.setdefault(lang, {})

        latest_date = (
            Thesaurus.objects.filter(identifier=I18N_THESAURUS_IDENTIFIER).values_list("date", flat=True).first()
        )

        if request_date == latest_date:
            # no changes after processing, set the info right away
            logger.debug(f"Caching lang:{lang} key:{data_key} date:{request_date}")
            cached_entry.update({"date": latest_date, data_key: data})
        else:
            logger.warning(
                f"Cache will not be updated for lang:{lang} key:{data_key} reqdate:{request_date} latest:{latest_date}"
            )

    def get_labels(self, lang):
        date, labels = self.get_entry(lang, self.DATA_KEY_LABELS)
        if labels is None:
            labels = {i["about"]: i["label"] for i in get_localized_tkeywords(lang, I18N_THESAURUS_IDENTIFIER)}
            self.set(lang, self.DATA_KEY_LABELS, labels, date)

        return labels

    def clear_schema_cache(self):
        logger.info("Clearing schema cache")
        while True:
            try:
                self.cache.popitem()
            except KeyError:
                return


def thesaurus_changed(sender, instance, **kwargs):
    if instance.identifier == I18N_THESAURUS_IDENTIFIER:
        if hasattr(instance, "_signal_handled"):  # avoid signal recursion
            return
        logger.debug(f"Thesaurus changed: {instance.identifier}")
        _update_thesaurus_date()


def thesaurusk_changed(sender, instance, **kwargs):
    if instance.thesaurus.identifier == I18N_THESAURUS_IDENTIFIER:
        logger.debug(f"ThesaurusKeyword changed: {instance.about} ALT:{instance.alt_label}")
        _update_thesaurus_date()


def thesauruskl_changed(sender, instance, **kwargs):
    if instance.keyword.thesaurus.identifier == I18N_THESAURUS_IDENTIFIER:
        logger.debug(
            f"ThesaurusKeywordLabel changed: {instance.keyword.about} ALT:{instance.keyword.alt_label} L:{instance.lang}"
        )
        _update_thesaurus_date()


def _update_thesaurus_date():
    logger.debug("Updating label thesaurus date")
    # update timestamp to invalidate other processes also
    i18n_thesaurus = Thesaurus.objects.get(identifier=I18N_THESAURUS_IDENTIFIER)
    i18n_thesaurus.date = datetime.now().replace(microsecond=0).isoformat()
    i18n_thesaurus._signal_handled = True
    i18n_thesaurus.save()
