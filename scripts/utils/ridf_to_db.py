from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from geonode.cephgeo.models import RIDF
from geonode.layers.models import Layer
from collections import defaultdict
from pprint import pprint
import traceback
import csv
import os
import codecs
from osgeo import ogr
import shapely
from shapely.wkb import loads
from django.db.models import Q
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def map_layer_floodplain(params):
    layer_list = Layer.objects.filter(
        typename__icontains=params['muni_prov'])
    # pprint(ridf_list)
    for layer in layer_list:
        layer.keywords.add(params['floodplain'])
        layer.save()


def map_ridf_floodplain(params):
    ridf_list = RIDF.objects.filter(
        layer_name__icontains=params['muni_prov'])
    # pprint(ridf_list)
    for muni_prov in ridf_list:
        muni_prov.riverbasins.add(params['floodplain'])
        muni_prov.save()


def _put_value_in_dict(municipality, province, _100yr, _25yr, _5yr):
    _dict = {'municipality': municipality,
             'province': province,
             '_100yr': _100yr,
             '_25yr': _25yr,
             '_5yr': _5yr}
    return _dict


def _parse_floodplain_csv(csv_path, msg):

    if not os.path.isfile(csv_path):
        print '{0} file not found'.format(msg)
    else:
        ridf_list = RIDF.objects.all()
        with codecs.open(csv_path, 'r', 'utf-8') as open_file:
            of = open_file.read()
            first_line = True
            second_line = True
            _list = []

            for line in of.split('\n'):
                tokens = line.strip().split(',')

                if first_line:
                    first_line = False
                    continue
                if second_line:
                    second_line = False
                    continue
                if line:
                    try:
                        # print tokens
                        params = {}
                        muni_prov = tokens[1].lower().strip(
                        ) + '_' + tokens[2].lower().strip()

                        tokens[0] = str(tokens[0])
                        if tokens[0] is not '':
                            # print tokens[0]
                            floodplain = tokens[0].strip()

                        params['floodplain'] = floodplain
                        params['muni_prov'] = muni_prov
                        _list.append(params)
                        map_layer_floodplain(params)
                        map_ridf_floodplain(params)

                    except Exception as e:
                        print e.message


def insert_pl1_floodplain():
    csv_path = os.path.realpath('/home/dj/geonode/docs/Phil-LiDAR1-RB-FP.csv')
    msg = 'Phil LiDAR 1 RB-FP CSV'
    _parse_floodplain_csv(csv_path, msg)


def insert_dream_floodplain():
    csv_path = os.path.realpath('/home/dj/geonode/docs/DREAM-RB_FP.csv')
    msg = 'DREAM RB-FP CSV'
    _parse_floodplain_csv(csv_path, msg)


def _parse_ridf_muni_csv():

    csv_path = os.path.realpath('/home/dj/geonode/docs/RIDF_municipality.csv')
    if not os.path.isfile(csv_path):
        print 'RIDF Municipality CSV file not found'
    else:
        with codecs.open(csv_path, 'r', 'utf-8') as open_file:
            of = open_file.read()
        # with open(csv_path, 'r') as open_file:
            first_line = True

            # reader = csv.reader(open_file, delimiter=',', quotechar='"')
            muni_prov_list = []
            # prev_muni_prov = ''
            # prev_ridf = []
            prev_row = {}
            # for line in reader:
            for line in of.split('\n'):

                tokens = line.strip().replace('"', '').split(',')

                # skip headers
                if first_line:
                    first_line = False
                    continue

                if line:
                    try:

                        # tokens = line[0].split(',')
                        # municipality = tokens[0].strip().decode('utf-8')
                        # province = tokens[1].strip().decode('utf-8')
                        # _100yr = float(line[1].strip())
                        # _25yr = float(line[2].strip())
                        # _5yr = float(line[3].strip())

                        municipality = tokens[0].strip()
                        province = tokens[1].strip()
                        _100yr = float(tokens[2].strip())
                        _25yr = float(tokens[3].strip())
                        _5yr = float(tokens[4].strip())

                        if not prev_row:
                            prev_row = _put_value_in_dict(
                                municipality, province, _100yr, _25yr, _5yr)
                        if (prev_row['municipality'] == municipality and
                                prev_row['province'] == province):
                            if _100yr >= prev_row['_100yr']:
                                prev_row = _put_value_in_dict(
                                    municipality, province, _100yr, _25yr, _5yr)
                        else:

                            params = {}
                            params = _put_value_in_dict(
                                # prev_row['municipality'].lower(),
                                # prev_row['province'].lower(),
                                prev_row['municipality'].lower(),
                                prev_row['province'].lower(),
                                prev_row['_100yr'],
                                prev_row['_25yr'],
                                prev_row['_5yr'])
                            params['_muni_prov'] = (prev_row['municipality']
                                                    + '_' +
                                                    prev_row['province']).lower()
                            muni_prov_list.append(params)
                            muni_prov_obj = RIDF(
                                municipality=params['municipality'],
                                province=params['province'],
                                _100yr=params['_100yr'],
                                _25yr=params['_25yr'],
                                _5yr=params['_5yr'],
                                layer_name=params['_muni_prov'])
                            muni_prov_obj.save()

                            prev_row = _put_value_in_dict(
                                municipality, province, _100yr, _25yr, _5yr)
                        # muni_prov_obj = RIDF(municipality=municipality, province=province, _100yr=_100yr, _25yr=_25yr,_5yr=_5yr,_muni_prov=_muni_prov)
                        # muni_prov_obj.save()

                    except Exception as e:
                        traceback.print_exc()
                        print(repr(line))
            params = {}
            params = _put_value_in_dict(
                prev_row['municipality'].lower(),
                prev_row['province'].lower(),
                prev_row['_100yr'],
                prev_row['_25yr'],
                prev_row['_5yr'])
            params['_muni_prov'] = (prev_row[
                'municipality'] + '_' + prev_row['province']).lower()
            # muni_prov_list.append(params)
            muni_prov_obj = RIDF(
                municipality=params['municipality'],
                province=params['province'],
                _100yr=params['_100yr'],
                _25yr=params['_25yr'],
                _5yr=params['_5yr'],
                layer_name=params['_muni_prov'])
            muni_prov_obj.save()

            # return muni_prov_list


def insert_nscb_code():
    # connect to db
    # assume layer lipad_gadm_ncsb exists
    if "lipad" not in settings.BASEURL:
        source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(
            settings.HOST_ADDR, settings.GIS_DATABASE_NAME,
            settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
    else:
        source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format(
            settings.DATABASE_HOST, settings.DATASTORE_DB,
            settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
    gadm_reference = source.GetLayer('lipad_gadm_ncsb')  # name typo
    ridf_list = RIDF.objects.all()

    for i,feature in enumerate(gadm_reference):
        # hop one is to one lang
        ridfs = RIDF.objects.filter(Q(province__icontains=feature.GetFieldAsString('province'))
                                         & Q(municipality__icontains=feature.GetFieldAsString
                                             ('citymunic')))
        if len(ridfs) == 1 and ridfs is not None:
            ridf_obj = ridfs[0]
            ridf_obj.nscb_code = int(feature.GetFieldAsString('nscb_code'))
            ridf_obj.save()
        else:
            for r in ridfs:
                print >>sys.stderr, '#',i,'More than one queryset filter in RIDF model or GADM_NCSB shapefile muni: ', r.municipality, 'province: ', r.province

    sys.stdout.flush()
    sys.stderr.flush()


if __name__ == '__main__':

    # print('Initialize db...')
    # dbcon, dbcur = _init_db()
    # print('Reading RIDF_Municipality list')
    # call this function once
    ridf_muni_list = _parse_ridf_muni_csv()

    # print('Inserted into geonode db')
    # pprint(sorted(ridf_muni_list, key=(lambda x: x['_muni_prov'])))
    # pprint(len(ridf_muni_list))
    # for i in sorted(ridf_muni_list, key=(lambda x: x['_muni_prov'])):
    #     print(i)
    # print('Data inserted to geonode')

    insert_pl1_floodplain()
    insert_dream_floodplain()

    # write nscb to RIDF model
    # RIDF must have all contents in database, lipad_gadm_ncsb.shp must be
    # uploaded in lipad_instance
    insert_nscb_code()
