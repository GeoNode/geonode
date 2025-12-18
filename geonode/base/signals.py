import logging
from datetime import datetime

from django.db.models.signals import post_save

from geonode.base.i18n import I18N_THESAURUS_IDENTIFIER
from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel

logger = logging.getLogger(__name__)


def connect_signals():
    logger.debug("Setting up signal connections...")
    post_save.connect(thesaurus_changed, sender=Thesaurus, weak=False, dispatch_uid="metadata_reset_t")
    post_save.connect(thesaurusk_changed, sender=ThesaurusKeyword, weak=False, dispatch_uid="metadata_reset_tk")
    post_save.connect(thesauruskl_changed, sender=ThesaurusKeywordLabel, weak=False, dispatch_uid="metadata_reset_tkl")
    logger.debug("Signal connections set")


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
