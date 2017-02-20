from geonode.geoserver.helpers import ogc_server_settings
from geoserver.catalog import Catalog
from geonode.layers.models import Style
import geonode.settings as settings
from celery.utils.log import get_task_logger
logger = get_task_logger("geonode.tasks.update")


def style_update(layer, style_template):
<<<<<<< HEAD

    # Get geoserver catalog
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])

    # Get equivalent geoserver layer
    gs_layer = cat.get_layer(layer.name)
    print layer.name, ': gs_layer:', gs_layer.name

    # Get current style
    # pprint(dir(gs_layer))
    cur_def_gs_style = gs_layer._get_default_style()
    # pprint(dir(cur_def_gs_style))
    if cur_def_gs_style is not None:
        print layer.name, ': cur_def_gs_style.name:', cur_def_gs_style.name

    # Get proper style
    attributes = [a.attribute for a in layer.attributes]
    gs_style = None
    if '_fh' in layer.name:
        if 'Var' in attributes:
            gs_style = cat.get_style(style_template)
        elif 'Merge' in attributes:
            gs_style = cat.get_style("fhm_merge")
        elif 'UVar' in attributes:
            gs_style = cat.get_style('fhm_uvar')
    else:
        gs_style = cat.get_style(style_template)

    # has_layer_changes = False
    try:
        if gs_style is not None:
            print layer.name, ': gs_style.name:', gs_style.name

            if cur_def_gs_style and cur_def_gs_style.name != gs_style.name:

                print layer.name, ': Setting default style...'
                gs_layer._set_default_style(gs_style)
                cat.save(gs_layer)

                print layer.name, ': Deleting old default style from geoserver...'
                cat.delete(cur_def_gs_style)

                print layer.name, ': Deleting old default style from geonode...'
                gn_style = Style.objects.get(name=layer.name)
                gn_style.delete()
    except Exception as e:
        logger.exception("Error setting style")
        # traceback.print_exc()
=======
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])
    gs_layer = cat.get_layer(layer.name)
    logger.info("GS LAYER: %s ", gs_layer.name)

    attributes = [a.attribute for a in layer.attributes]
    style = None
    if 'fh' in layer.name:
        if 'Var' in attributes:
            style = cat.get_style(style_template)
        elif 'Merge' in attributes:
            style = cat.get_style("fhm_merge")
    else:
        style = cat.get_style(style_template)

    if style is not None:
        try:

            gs_layer._set_default_style(style)
            cat.save(gs_layer)
            gs_style = cat.get_style(layer.name)
            if gs_style:
                logger.info("GS STYLE: %s " % gs_style.name)
                logger.info("Geoserver: Will delete style %s ", gs_style.name)
                cat.delete(gs_style)
                gn_style = Style.objects.get(name=layer.name)
                logger.info("Geonode: Will delete style %s ", gn_style.name)
                gn_style.delete()

            layer.sld_body = style.sld_body
            layer.save()
        except Exception as e:
            logger.exception("Error setting style")
            # traceback.print_exc()
>>>>>>> master
