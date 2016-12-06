#!/usr/bin/env python

# Script for updating metadata of already uploaded flood hazard maps
# Applicable only for layers renamed using PSA code
# Uses new RIDF model with the ff cols:
#       ID, prov_code, prov_name, muni_code, muni_name, iscity,
#       5yr, 25yr, 100yr, rbs_raw, riverbasins
# Inserts RIDF value into metadata description of a layer
# Uses PSA code to properly rename layer title into: Municaplity, Province etc
# Tags riverbasin as keywords to layers
# riverbasin gotten from FMC spreadsheet

from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from geonode.cephgeo.models import RIDF
from geonode.layers.models import Layer
from pprint import pprint
from django.db.models import Q
from datetime import datetime
from geoserver.catalog import Catalog
from geonode.layers.models import Style
from geonode.base.models import TopicCategory
import os, subprocess
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

def fh_perms_update(layer):
    try:
        layer.remove_all_permissions()
        anon_group = Group.objects.get(name='anonymous')
        assign_perm('view_resourcebase', anon_group, layer.get_self_resource())
        assign_perm('download_resourcebase', anon_group,
                    layer.get_self_resource())
        assign_perm('view_resourcebase', get_anonymous_user(),
                    layer.get_self_resource())
        assign_perm('download_resourcebase', get_anonymous_user(),
                    layer.get_self_resource())
    except:
        # ts = time.time()
        # st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        # Err_msg = st + " Error in updating permission of " + layer.name + "\n"
        Err_msg = " Error in updating permission of " + layer.name + "\n"
        pass

def style_update(layer, style_template):
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                  username=settings.OGC_SERVER['default']['USER'],
                  password=settings.OGC_SERVER['default']['PASSWORD'])
    try:
        layer_attrib = layer.attributes[0].attribute.encode("utf-8")
    except Exception as e:
            print "No layer attribute %s" % e
    ctr = 0

    if 'fh' in layer.name:
        style = None
        if layer_attrib == "Var":
            style = cat.get_style(style_template)
        else:
            style = cat.get_style("fhm_merge")
    else:
        style = cat.get_style(style_template)

    if style is not None:
        try:
            gs_layer = cat.get_layer(layer.name)
            print "GS LAYER: %s " % gs_layer.name
            gs_layer._set_default_style(style)
            cat.save(gs_layer)
            ctr+=1
            gs_style = cat.get_style(layer.name)
            if gs_style:
                print "GS STYLE: %s " % gs_style.name
                print "Geoserver: Will delete style %s " % gs_style.name
                cat.delete(gs_style)
                gn_style = Style.objects.get(name=layer.name)
                print "Geonode: Will delete style %s " % gn_style.name
                gn_style.delete()

            layer.sld_body = style.sld_body
            layer.save()
        except Exception as e:
            # print "%s" % e
            traceback.print_exc()


    # if gs_style is not None:
    #     try:

    #         gn_style = Style.objects.get(name=style_template)
    #         #update in geoserver
    #         gs_layer = cat.get_layer(layer.name)
    #         print "GS LAYER: %s " % gs_layer.name
    #         gs_layer._set_default_style(gs_style)
    #         gs_layer._set_alternate_styles([gs_style])
    #         cat.save(gs_layer)
    #         #update in geonode
    #         layer.default_style = gn_style
    #         layer.save()
    #         #delete in geonode
    #         gn_orig_style = Style.objects.get(name=layer.name)
    #         lstyles = layer.styles
    #         try:
    #             lstyles.remove(gn_orig_style)
    #         except:
    #             traceback.print_exc()
    #         try:
    #             gn_orig_style.delete()
    #         except:
    #             traceback.print_exc()
    #         #delete in geoserver
    #         gs_orig_style = cat.get_style(layer.name)
    #         if gs_orig_style is not None:
    #             cat.delete(gs_orig_style)

    #         style.sld_title = style_template
    #         style.save()

    #     except Exception as e:
    #         #print "%s" % e
    #         raise

def ridf_value(muni_code, flood_year):
    # ridf_obj = RIDF.objects.get(muni_code__icontains=muni_code)

    if ridf_obj is not None:
        if flood_year == 5:
            return ridf_obj._5yr
        elif flood_year == 25:
            return ridf_obj._25yr
        elif flood_year == 100:
            return ridf_obj._100yr
    else:
        return 'N/A'


def muni_code_title(muni_code, layername, flood_year):
    # layer.title = layer.name.replace("_10m","").replace("_30m","").replace("__"," ").
    # replace("_"," ").replace("fh%syr" % flood_year,"%s Year Flood Hazard Map" % flood_year).title()
    ridf_obj = RIDF.objects.get(muni_code__icontains=muni_code)
    if ridf_obj is not None:
        muni = ridf_obj.muni_name
        prov = ridf_obj.prov_name
        title = layer.name.replace("_10m", "").replace("_30m", "").replace("__", " ").replace("_", " ").replace(
            '{0}'.format(psa_code), '{0}, {1} {2} Year Flood Hazard Map'.format(muni, prov, flood_year)).title()
        return title
    else:
        return 'N/A'


# def tag_riverbasin(layer):

#     for tag in ridf_obj.riverbasins.all():
#         layer.keywords.add(tag)


def fhm_year_metadata(flood_year):
    flood_year_probability = int(100 / flood_year)
    layer_list = []
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    layer_list = Layer.objects.filter(Q(
        name__iregex=r'^ph[0-9]+_fh' + str(flood_year)) & Q(upload_session__date__month=month) & Q(
        upload_session__date__day=day) & Q(upload_session__date__year=year))
    total_layers = len(layer_list)
    print("Updating metadata of [{0}] Flood Hazard Maps for Flood Year [{1}]".format(
        total_layers, flood_year))
    ctr = 0

    for layer in layer_list:
        try:
            print "Layer: %s" % layer.name
            style_update(layer,'fhm')
            fh_perms_update(layer)
            # batch_seed(layer)

            map_resolution = ''

            if "_10m_30m" in layer.name:
                map_resolution = '30'
            elif "_10m" in layer.name:
                map_resolution = '10'
            elif "_30m" in layer.name:
                map_resolution = '30'

            # print "Layer: %s" % layer.name
            # layer.title = layer.name.replace("_10m","").replace("_30m","").replace("__"," ").replace("_"," ").replace("fh%syr" % flood_year,"%s Year Flood Hazard Map" % flood_year).title()

            # Use nscb for layer title
            muni_code = layer.name.split('_fh')[0]
            print 'muni_code: {0}'.format(muni_code)
            ridf_obj = RIDF.objects.get(muni_code__icontains=muni_code)
            ridf = eval('ridf_obj._' + str(flood_year) + 'yr')
            print 'ridf:', ridf

            muni = ridf_obj.muni_name
            prov = ridf_obj.prov_name
            layer.title = '{0}, {1} {2} Year Flood Hazard Map'.format(
                muni, prov, flood_year).replace("_", " ").title()
            if ridf_obj.iscity:
                layer.title = 'City of ' + layer.title
            print 'layer.title:', layer.title

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
            ctr += 1
            print "[{0} YEAR FH METADATA] {1}/{2} : {3}".format(flood_year, ctr, total_layers, layer.title)

        except Exception as e:
            print "%s" % e
            pass

        # break


def fhm_metadata_update(flood_years=(5, 25, 100)):
    for year in flood_years:
        fhm_year_metadata(year)
        # break

if __name__ == '__main__':
    fhm_metadata_update()
    