import logging
import threading
import time

from django.db import connection
from django.utils.translation import get_language, gettext as _

from geonode.base.models import ThesaurusKeywordLabel, Thesaurus

logger = logging.getLogger(__name__)

I18N_THESAURUS_IDENTIFIER = "labels-i18n"
OVR_SUFFIX = "__ovr"


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
    with connection.cursor() as cursor:
        cursor.execute(query, [f"{lang}%", thesaurus_identifier])
        for id, about, alt, label, dblang in cursor.fetchall():
            if not dblang or dblang == lang:
                # this is a properly localized label or an altlabel (when dblang is null)
                ret[id] = {"id": id, "about": about, "label": label, "default": alt}
            else:
                logger.warning(f"Found unexpected lang {dblang}")

    return sorted(ret.values(), key=lambda i: i["about"].lower())


# TODO: deprecate and use LabelResolver.gettext()
def get_localized_label(lang, about):
    # look for override
    ovr_qs = ThesaurusKeywordLabel.objects.filter(
        keyword__thesaurus__identifier=I18N_THESAURUS_IDENTIFIER, keyword__about=f"{about}{OVR_SUFFIX}", lang=lang
    )
    if ovr_qs.exists():
        return ovr_qs.values_list("label", flat=True).first()

    # return requested keyword, if any
    return (
        ThesaurusKeywordLabel.objects.filter(
            keyword__thesaurus__identifier=I18N_THESAURUS_IDENTIFIER, keyword__about=about, lang=lang
        )
        .values_list("label", flat=True)
        .first()
    )


class I18nCacheEntry:
    def __init__(self):
        # the date field of the thesaurus when it was last loaded, it's used for the expiration check
        self.date: str = "init"
        self.caches: dict = {}  # the caches for this language

    def __str__(self):
        return f"I18nCacheEntry {self.date} [{list(self.caches.keys())}]"


class I18nCache:
    """
    Caches language related data.
    Synch is performed via date field in the "labels-i18n" thesaurus.
    """

    CHECK_INTERVAL = 5  # seconds

    def __init__(self):
        # the cache has the lang as key, and I18nCacheEntry as a value:
        self.lang_cache = {}
        self._last_check = 0
        self._lock = threading.Lock()

    def get_entry(self, lang, data_key):
        """
        returns date:str, data
        date is needed for checking the entry freshness when setting info
        data may be None if not cached or expired
        """
        with self._lock:
            cached_entry: I18nCacheEntry = self.lang_cache.get(lang, None)

            time_now = time.time()
            needs_check = time_now - self._last_check > I18nCache.CHECK_INTERVAL

            # if not needs_check:
            #     logger.debug(f"No cache check needed {lang}:{data_key} @ {cached_entry}")
            # else:
            #     logger.debug(f"Cache check needed {lang}:{data_key} @ {cached_entry}")

            if needs_check or not cached_entry:
                self._last_check = time_now
                thesaurus_date = (  # may be none if thesaurus does not exist
                    Thesaurus.objects.filter(identifier=I18N_THESAURUS_IDENTIFIER)
                    .values_list("date", flat=True)
                    .first()
                )
                if cached_entry and cached_entry.date != thesaurus_date:
                    logger.info(f"Cache for {lang}:{data_key} needs to be recreated")
                    return thesaurus_date, None
                if not cached_entry:
                    logger.info(f"Cache for {lang}:{data_key} needs to be created")
                    return thesaurus_date, None

            # logger.debug(f"Returning cached entry for {lang}:{data_key} @ {cached_entry.date}")
            return cached_entry.date, cached_entry.caches.get(data_key, None)

    def set(self, lang: str, data_key: str, data, request_date: str):
        # TODO: check if lang is allowed
        cached_entry: I18nCacheEntry = self.lang_cache.setdefault(lang, I18nCacheEntry())

        latest_date = (
            Thesaurus.objects.filter(identifier=I18N_THESAURUS_IDENTIFIER).values_list("date", flat=True).first()
        )

        if request_date == latest_date:
            # no changes after processing, set the info right away
            logger.debug(f"Caching lang:{lang} key:{data_key} date:{request_date}")
            cached_entry.date = latest_date
            cached_entry.caches[data_key] = data
            return True
        else:
            logger.warning(
                f"Cache will not be updated for lang:{lang} key:{data_key} reqdate:{request_date} latest:{latest_date}"
            )
            return False

    def clear(self):
        logger.info("Clearing i18n cache")
        self.lang_cache.clear()

    def force_check(self):
        """For testing: forces a check against the DB on the next get_entry call."""
        self._last_check = 0


class LabelResolver:
    CACHE_KEY_LABELS = "labels"

    def gettext(self, key, lang=None, fallback=True):
        """
        Return the translated text in the label Thesaurus, falling back to the PO/MO translation.
        If fallback=False only search in the label Thesaurus, and may return None if not found
        """
        lang = lang or get_language()
        # TODO: implement the OVR search
        return self.get_labels(lang).get(key, None) or (_(key) if fallback else None)

    def get_labels(self, lang):
        date, labels = i18nCache.get_entry(lang, self.CACHE_KEY_LABELS)
        if labels is None:
            logger.debug("LabelResolver: loading I18N labels")
            labels = self._create_labels_cache(lang)
            i18nCache.set(lang, self.CACHE_KEY_LABELS, labels, date)
        return labels

    def _create_labels_cache(self, lang):
        labels = {}
        for i in get_localized_tkeywords(lang, I18N_THESAURUS_IDENTIFIER):
            about = i["about"]
            if about.endswith(OVR_SUFFIX) and not i["label"]:
                # we don't want default values for override entries
                continue
            labels[about] = i["label"] or i["default"]
        return labels


i18nCache = I18nCache()
labelResolver = LabelResolver()
gettext = labelResolver.gettext
