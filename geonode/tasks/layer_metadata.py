from celery import task, group
from celery.utils.log import get_task_logger
from datetime import datetime
from django.db.models import Q
from geonode.base.models import TopicCategory
from geonode.cephgeo.models import RIDF
from geonode.layers.models import Layer
from layer_permission import fhm_perms_update
from layer_style import style_update
logger = get_task_logger("geonode.tasks.update")


@task(name='geonode.tasks.update.update_fhm_metadata_task._update', queue='update')
def _update(layer, flood_year, flood_year_probability):
    try:
        logger.info('\n\n' + '#' * 80 + '\n')
        logger.info("Layer: %s", layer.name)
        style_update(layer, 'fhm')
        fhm_perms_update(layer)
        # batch_seed(layer)

        map_resolution = ''

        if "_10m_30m" in layer.name:
            map_resolution = '30'
        elif "_10m" in layer.name:
            map_resolution = '10'
        elif "_30m" in layer.name:
            map_resolution = '30'

        # logger.info "Layer: %s" % layer.name
        # layer.title = layer.name.replace("_10m","").replace("_30m","").replace("__"," ").replace("_"," ").replace("fh%syr" % flood_year,"%s Year Flood Hazard Map" % flood_year).title()

        # Use nscb for layer title
        muni_code = layer.name.split('_fh')[0]
        logger.info('muni_code: {0}'.format(muni_code))
        ridf_obj = RIDF.objects.get(muni_code__icontains=muni_code)
        ridf = eval('ridf_obj._' + str(flood_year) + 'yr')
        logger.info('ridf: %s', ridf)

        muni = ridf_obj.muni_name
        prov = ridf_obj.prov_name
        layer.title = '{0}, {1} {2} Year Flood Hazard Map'.format(
            muni, prov, flood_year).replace("_", " ").title()
        if ridf_obj.iscity:
            layer.title = 'City of ' + layer.title
        logger.info('layer.title: %s', layer.title)

        layer.abstract = """This shapefile, with a resolution of {0} meters, illustrates the inundation extents in the area if the actual amount of rain exceeds that of a {1} year-rain return period.

Note: There is a 1/{2} ({3}%) probability of a flood with {4} year return period occurring in a single year. The Rainfall Intesity Duration Frequency is {5}mm.

3 levels of hazard:
Low Hazard (YELLOW)
Height: 0.1m-0.5m

Medium Hazard (ORANGE)
Height: 0.5m-1.5m

High Hazard (RED)
Height: beyond 1.5m""".format(map_resolution, flood_year, flood_year, flood_year_probability, flood_year, ridf)

        layer.purpose = " The flood hazard map may be used by the local government for appropriate land use planning in flood-prone areas and for disaster risk reduction and management, such as identifying areas at risk of flooding and proper planning of evacuation."

        layer.keywords.add("Flood Hazard Map")
        # tag_riverbasin(layer)
        # for tag in ridf_obj.riverbasins.all():
        #     layer.keywords.add(tag)

        layer.category = TopicCategory.objects.get(
            identifier="geoscientificInformation")
        layer.save()
        # ctr += 1
        logger.info(
            "[{0} YEAR FH METADATA] {1}".format(flood_year, layer.title))

    except Exception:
        logger.exception("Error setting FHM metadata!")
        # pass


def fhm_year_metadata(flood_year):
    flood_year_probability = int(100 / flood_year)
    layer_list = []
    _date = datetime.now()
    year = _date.year
    month = _date.month
    day = _date.day
    # layer_list = Layer.objects.filter(Q(
    #     name__iregex=r'^ph[0-9]+_fh' + str(flood_year)) & Q(upload_session__date__month=month) & Q(
    #     upload_session__date__day=day) & Q(upload_session__date__year=year))
    layer_list = Layer.objects.filter(
        Q(name__iregex=r'^ph[0-9]+_fh' + str(flood_year)))
    total_layers = len(layer_list)
    logger.info("Updating metadata of [{0}] Flood Hazard Maps for Flood Year [{1}]".format(
        total_layers, flood_year))

    # for layer in layer_list:
    #     _update(layer, flood_year, flood_year_probability)

    jobs = group(_update(layer, flood_year, flood_year_probability) for layer in layer_list)
    result = jobs.apply_async()
