from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from geonode.cephgeo.models import RIDF
from geonode.layers.models import Layer
from pprint import pprint
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def cross_check_municpalities():

    if "lipad" not in settings.BASEURL:
        source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format
                           (settings.HOST_ADDR, settings.GIS_DATABASE_NAME,
                            settings.DATABASE_USER, settings.DATABASE_PASSWORD)))
    else:
        source = ogr.Open(("PG:host={0} dbname={1} user={2} password={3}".format
                           (settings.DATABASE_HOST, settings.DATASTORE_DB,
                            settings.DATABASE_USER, settings.DATABASE_PASSWORD)))

    # psa_adm_layer has 1627 rows
    psa_adm_layer = source.GetLayer('phl_adm3_psa_pn_2016june2')
    # RIDF model has 1647 rows
    ridf_objects = RIDF.objects.all()

    psa_rows = psa_adm_layer.GetLayerCount()
    ridf_rows = len(ridf_objects)

    pprint('PSA layer row count: {0} | RIDF model row count: {1}'.format(
        psa_rows, ridf_rows))
    # more_rows = ridf_objects
    ridf_more_rows = True
    if psa_rows > ridf_rows:
        ridf_more_rows = False

    # for index in more_rows
    # if ridf_more_rows:
    #     for obj in ridf_objects:
    #         for feature in psa_adm_layer:
    #             if obj.municipality == psa.a

    layer_name_list = []
    non_match_list_A = []
    non_match_list_B = []
    for feature in psa_adm_layer:
        query = RIDF.objects.filter(Q(municipality__icontains=feature.GetFieldAsString(
            'Mun_Name')) & Q(province__icontains=feature.GetFieldAsString('Pro_Name')))
        if len(query) > 1:
            pprint('PSA to RIDF model returned more than 1 instance of {0} , {1}'.format(
                feature.GetFieldAsString('Mun_Name'), feature.GetFieldAsString('Pro_Name')))
        elif query is None:
            pprint('No query match from PSA to RIDF model of {0} , {1}'.format(
                feature.GetFieldAsString('Mun_Name'), feature.GetFieldAsString('Pro_Name')))
            layer_name = feature.GetFieldAsString('Mun_Name') + ',' + feature.GetFieldAsString('Pro_Name')
            non_match_list_A.append(layer_name)
        elif len(query)==1 and query is not None:
            layer_name_list.append(query.layer_name)

    for obj in ridf_objects:
        if obj.layer_name not in layer_name_list:
            non_match_list_B.append(obj.layer_name)




if __name__ == '__main__':
    cross_check_municpalities()
