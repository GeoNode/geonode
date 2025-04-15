from geonode.base.management.command_utils import setup_logger
from geonode.base.models import Thesaurus

logger = setup_logger()


def list_thesauri():
    logger.info("List of existing thesauri:")

    thesaurus_entries = Thesaurus.objects.values_list("identifier", flat=True)
    if len(thesaurus_entries) == 0:
        logger.warning("No thesaurus found")
        return
    max_id_len = len(max(thesaurus_entries, key=len))

    for t in Thesaurus.objects.order_by("order").all():
        if t.card_max == 0:
            card = "DISABLED"
        else:
            # DISABLED
            # [0..n]
            card = f'[{t.card_min}..{t.card_max if t.card_max!=-1 else "N"}]  '
        logger.info(
            f'id:{t.id:2} sort:{t.order:3} {card} name={t.identifier.ljust(max_id_len)} title="{t.title}" URI:{t.about}\n'
        )
