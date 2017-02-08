import geonode.settings as settings

from celery.task import task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from geonode.base.models import TopicCategory
from geonode.documents.models import Document
from geonode.geoserver.helpers import gs_slurp, http_client, ogc_server_settings
from geonode.layers.models import Layer, Style
from geonode.layers.utils import create_thumbnail
from geonode.security.models import PermissionLevelMixin
from geoserver.catalog import Catalog
from guardian.shortcuts import assign_perm, get_anonymous_user
from layer_metadata import fhm_year_metadata
from layer_style import style_update
from lidar_coverage import lidar_coverage_metadata
from osgeo import ogr
from pprint import pprint
from pwd import getpwnam
from string import Template
from suc_rb_tagging import tag_layers
import datetime
import logging
import os
import psycopg2
import subprocess
import time
import traceback

logger = get_task_logger("geonode.tasks.update")
logger.setLevel(logging.INFO)


@task(name='geonode.tasks.update.fh_perms_update', queue='update')
def fh_perms_update(layer):
    # anonymous_group, created = Group.objects.get_or_create(name='anonymous')
    #layer_list = Layer.objects.filter(name__icontains='fh')
    #total_layers = len(layer_list)
    #ctr = 1
    # for layer in layer_list:

    try:
        # geoadmin = User.objects.get.filter(username='geoadmin')
        # for user in User.objects.all():
        layer.remove_all_permissions()
        anon_group = Group.objects.get(name='anonymous')
        assign_perm('view_resourcebase', anon_group, layer.get_self_resource())
        assign_perm('download_resourcebase', anon_group,
                    layer.get_self_resource())
        # superusers=get_user_model().objects.filter(Q(is_superuser=True))
        # for superuser in superusers:
        #     assign_perm('view_resourcebase', superuser, layer.get_self_resource())
        #     assign_perm('download_resourcebase', superuser, layer.get_self_resource())
        assign_perm('view_resourcebase', get_anonymous_user(),
                    layer.get_self_resource())
        assign_perm('download_resourcebase', get_anonymous_user(),
                    layer.get_self_resource())
        # print "[FH PERMISSIONS] {0}/{1} : {2} ".format(ctr,total_layers,layer.name)
        # layer.remove_all_permissions()
        # assign_perm('view_resourcebase', get_anonymous_user(), layer.get_self_resource())
        # assign_perm('download_resourcebase', get_anonymous_user(), layer.get_self_resource())
        # ctr+=1
    except:
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        Err_msg = st + " Error in updating style of " + layer.name + "\n"
        pass


def style_update(layer, style_template):
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])

    # layer_list = Layer.objects.filter(name__icontains='fh')#initial run of script includes all  layers for cleaning of styles in GN + GS
    # layer_list = Layer.objects.filter(name__icontains='fh').exclude(styles__name__icontains='fhm'
    # total_layers = len(layer_list)
    try:
        layer_attrib = layer.attributes[0].attribute.encode("utf-8")
    except Exception:
        logger.exception('No layer attribute!')
    ctr = 0
    # for layer in layer_list:
    # print "[FH STYLE] {0}/{1} : {2} ".format(ctr,total_layers,layer.name)
    # delete thumbnail first because of permissions

    if '_fh' in layer.name:
        if layer_attrib == "Var":
            gs_style = cat.get_style(style_template)
        else:
            gs_style = cat.get_style("fhm_merge")
    else:
        gs_style = cat.get_style(style_template)

    if gs_style is not None:
        try:
            gn_style = Style.objects.get(name=style_template)
            # update in geoserver
            gs_layer = cat.get_layer(layer.name)
            logger.info('GS LAYER: %s', gs_layer.name)
            gs_layer._set_default_style(gs_style)
            gs_layer._set_alternate_styles([gs_style])
            cat.save(gs_layer)
            # update in geonode
            layer.default_style = gn_style
            layer.save()
            # delete in geonode
            gn_orig_style = Style.objects.get(name=layer.name)
            lstyles = layer.styles
            try:
                lstyles.remove(gn_orig_style)
            except:
                traceback.print_exc()
            try:
                gn_orig_style.delete()
            except:
                traceback.print_exc()
            # delete in geoserver
            gs_orig_style = cat.get_style(layer.name)
            if gs_orig_style is not None:
                cat.delete(gs_orig_style)

            style.sld_title = style_template
            style.save()

        except Exception as e:
            # print "%s" % e
            raise


def iterate_over_layers(layers, style_template):
    count = len(layers)
    for i, layer in enumerate(layers):
        try:
            print "Layer {0} {1}/{2}".format(layer.name, i + 1, count)
            # print "Layer {0}".format(layers.name)
            # layer.default_style = layer.styles.get()
            # layer.save()
            if style_template == '':
                print "Layer {0} - style template is {1} ".format(layer.name, style_template)
                layer.default_style = layer.styles.get()
                layer.save()
            else:
                style_update(layer, style_template)
        except Exception as e:
            # print "%s" % e
            # pass
            print 'Error setting style!'
            traceback.print_exc()
            return


@task(name='geonode.tasks.update.layer_default_style', queue='update')
def layer_default_style(keyword):
    # put try-except
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])

    if keyword == 'jurisdict':
        try:
            layers = Layer.objects.filter(
                owner__username="dataRegistrationUploader")
            for l in layers:
                gs_layer = cat.get_layer(l.name)  # geoserver layer object
                # if gs_layer.default_style.name != 'Boundary':
                #     layers.remove(l)
            iterate_over_layers(layers, 'Boundary')
        except Exception as e:
            print "%s" % e
            pass
    elif keyword == 'dem_':
        try:
            layers = Layer.objects.filter(name__icontains=keyword)
            iterate_over_layers(layers, '')
        except Exception as e:
            print "%s" % e
            pass
    elif keyword == 'Hazard':
        try:
            # layers = Layer.objects.filter(keywords__name__icontains=keyword)
            layers = Layer.objects.filter(name__icontains='_fh')
            iterate_over_layers(layers, 'fhm')
        except Exception as e:
            print "%s" % e
            pass
    elif keyword == 'PhilLiDAR2':
        try:
            layers = Layer.objects.filter(keywords__name__icontains=keyword)
            iterate_over_layers(layers, '')
        except Exception as e:
            print "%s" % e
            pass
    elif keyword == 'SAR':
        try:
            # layers = Layer.objects.filter(keywords__name__icontains=keyword)
            layers = Layer.objects.filter(name__icontains='sar_')
            iterate_over_layers(layers, 'DEM')
        except Exception as e:
            print "%s" % e
            pass


@task(name='geonode.tasks.update.seed_layers', queue='update')
def seed_layers(keyword):
    layer_list = Layer.objects.filter(keywords__name__icontains=keyword)
    for layer in layer_list:
        try:
            out = subprocess.check_output([settings.PROJECT_ROOT + '/gwc.sh', 'seed',
                                           '{0}:{1}'.format(
                                               layer.workspace, layer.name), 'EPSG:4326', '-v', '-a',
                                           settings.OGC_SERVER['default']['USER'] + ':' +
                                           settings.OGC_SERVER['default'][
                                               'PASSWORD'], '-u',
                                           settings.OGC_SERVER['default']['LOCATION'] + 'gwc/rest'],
                                          stderr=subprocess.STDOUT)
            print out
        except subprocess.CalledProcessError as e:
            print 'Error seeding layer:', layer
            print 'e.returncode:', e.returncode
            print 'e.cmd:', e.cmd
            print 'e.output:', e.output


def _get_ridf(layer_name, flood_year):
    print ''
    # layer.name = municipality_province_fh{year}yr_mapresolution
    tokens = layer_name.split('_fh').strip()
    layer_muni_prov = tokens[0]

    # ridf = RIDF.objects.filter(Q(layer_name=layer_muni_prov)&Q())


@task(name='geonode.tasks.update.update_lidar_coverage_task', queue='update')
def update_lidar_coverage_task():
    # for year in flood_years:
    #     fhm_year_metadata(year)
    lidar_coverage_metadata()


@task(name='geonode.tasks.update.update_fhm_metadata_task', queue='update')
def update_fhm_metadata_task(flood_years=(5, 25, 100)):
    # for year in flood_years:
    #     fhm_year_metadata(year)
    fhm_year_metadata(100)


@task(name='geonode.tasks.update.sar_metadata_update', queue='update')
def sar_metadata_update():

    ###############################
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])

    count_notification = Template(
        '[$ctr/$total] Editing Metadata for Layer: $layername')

    ###
    #   SAR
    #   with sld template
    ###
    filter_substring = 'sar_'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    total = len(layer_list)
    ctr = 0
    title = Template('$area SAR DEM')

    for layer in layer_list:
        ctr += 1
        print "Layer: %s" % layer.name
        # style_update(layer,'dem')
        text_split = layer.name.split(filter_substring)
        area = text_split[1].title().replace(
            '_', ' ')  # from sar_area to ['','area']
        print count_notification.substitute(ctr=ctr, total=total, layername=layer.name)
        layer.title = title.substitute(area=area)
        layer.abstract = """All Synthetic Aperture Radar digital elevation models was acquired from MacDonald, Dettwiler and Associates Ltd. (MDA), British Columbia, Canada and post-processed by the UP Training Center for Applied Geodesy and Photogrammetry (UP-TCAGP), through the DOST-GIA funded Disaster Risk and Exposure Assessment for Mitigation (DREAM) Program.

            Projection:     WGS84 UTM Zone 51
            Resolution:     10 m
            Tile Size:  10km by 10km
            Absolute vertical map accuracy: LE 90
            Date of Acquisition: February 21, 2012-September 13, 2013
            """
        layer.keywords.add("SAR")
        layer.save()


@task(name='geonode.tasks.update.pl2_metadata_update', queue='update')
def pl2_metadata_update():
    # fix this
    pass


@task(name='geonode.tasks.update.geoserver_update_layers', queue='update')
def geoserver_update_layers(*args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@task(name='geonode.tasks.update.create_document_thumbnail', queue='update')
def create_document_thumbnail(object_id):
    """
    Runs the create_thumbnail logic on a document.
    """

    try:
        document = Document.objects.get(id=object_id)

    except Document.DoesNotExist:
        return

    image = document._render_thumbnail()
    filename = 'doc-%s-thumb.png' % document.id
    document.save_thumbnail(filename, image)


@task(name='geonode.tasks.update.floodplain_keywords', queue='update')
def floodplain_keywords():

    source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format
                       (settings.DATABASE_HOST, settings.GIS_DATABASE_NAME,
                        settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
    conn = psycopg2.connect(("host={0} dbname={1} user={2} password={3}".format
                             (settings.DATABASE_HOST, settings.GIS_DATABASE_NAME,
                              settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
    cur = conn.cursor()

    tag_layers('dream', settings.RB_DELINEATION_DREAM,
               cur, conn, source)
    tag_layers('', settings.FP_DELINEATION_PL1, cur, conn, source)
