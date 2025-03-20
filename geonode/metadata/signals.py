import logging

from django.db.models.signals import post_save

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel
from geonode.metadata.manager import thesaurus_changed, thesaurusk_changed, thesauruskl_changed

logger = logging.getLogger(__name__)


def connect_signals():
    logger.debug("Setting up signal connections...")
    post_save.connect(thesaurus_changed, sender=Thesaurus, weak=False, dispatch_uid="metadata_reset_t")
    post_save.connect(thesaurusk_changed, sender=ThesaurusKeyword, weak=False, dispatch_uid="metadata_reset_tk")
    post_save.connect(thesauruskl_changed, sender=ThesaurusKeywordLabel, weak=False, dispatch_uid="metadata_reset_tkl")
    logger.debug("Signal connections set")
