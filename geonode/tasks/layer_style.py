from geonode.geoserver.helpers import ogc_server_settings
from geoserver.catalog import Catalog
from geonode.layers.models import Style
import geonode.settings as settings
from celery.utils.log import get_task_logger
logger = get_task_logger("geonode.tasks.update")


def update_style(layer, style_template):

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
