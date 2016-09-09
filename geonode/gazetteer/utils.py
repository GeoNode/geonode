from array import array
import logging
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from geonode.gazetteer.models import GazetteerEntry
#from psycopg2 import extras
from geonode.gazetteer.models import GazetteerEntry
from geopy import geocoders
from django.conf import settings
import psycopg2
from django.db.models import Q
from geonode.maps.models import Layer, LayerAttribute, MapLayer, Map
from django.core.cache import cache
from geonode.flexidates import parse_julian_date
import re

GAZETTEER_TABLE = 'gazetteer_gazetteerentry'

__author__ = 'mbertrand'

logger = logging.getLogger("geonode.gazetteer.utils")

'''
ALTER TABLE gazetteer_gazetteerentry ADD COLUMN placename_tsv tsvector;
CREATE INDEX placename_tsv_index on gazetteer_gazetteerentry using gin(placename_tsv);
UPDATE gazetteer_gazetteerentry SET text_search =
     to_tsvector('english', coalesce(place_name,''));
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
  ON gazetteer_gazetteerentry FOR EACH ROW EXECUTE PROCEDURE
  tsvector_update_trigger(placename_tsv, 'pg_catalog.english', place_name);
'''

def get_geometry_type(layer):
    """
    Return the geometry type (POINT, POLYGON etc), geometry column name, and projection of a layer
    """
    conn = getConnection(layer.store)
    try:
        cur = conn.cursor()
        cur.execute("select type, f_geometry_column, srid from geometry_columns where f_table_name = '%s'" % layer.name)
        result = cur.fetchone()
        return result
    except Exception, e:
        logger.error("Error retrieving type for PostGIS table %s:%s", layer.name, str(e))
        raise
    finally:
        conn.close()


def getGazetteerEntry(input_id):

    try:
        results = GazetteerEntry.objects.filter(id=input_id)
        posts = []
        for entry in results:
            posts.append({'placename': entry.place_name, 'coordinates': (entry.longitude, entry.latitude),
                          'source': formatSourceLink(entry.layer_name), 'id': entry.id})
        return posts
    except Exception, e:
        logger.error("Error retrieving results for gazetteer by id %d:%s", input_id, str(e))
        raise



def formatSourceLink(layer_name):
    layer = cache.get("layerinfo_" + layer_name)
    if layer is None:
        layer = Layer.objects.get(name=layer_name)
        cache.add("layerinfo_" + layer_name, layer)
    return "<a href='{0}data/{1}' target='_blank'>{2}</a>".format(settings.SITEURL, layer.typename, layer.name)


def getGazetteerResults(place_name, map=None, layer=None, start_date=None, end_date=None, project=None, user=None):
    """
    Return placenames from gazetteer that match certain filters:
        place_name: text to do a LIKE search for
        map: search all layers that are present in this map (map id)
        layer: search only this layer (layer name)
        start_date: return only matches with a start date >= this value
        end_date: return only matches with an end date <= this value
        project: only return matches within the specified project
    """

    layers = []
    if map:
        mapObject = get_object_or_404(Map, pk=map)
        maplayers = MapLayer.objects.filter(map=mapObject.id)
        for maplayer in maplayers:
            try:
                layer = Layer.objects.get(typename=maplayer.name)
                layers.append(layer.name)
            except:
                logger.info("Could not find %s", maplayer.name)

    elif layer:
        layers = [layer]

    ## The following retrieves results using the GazetteerEntry model.

    criteria = Q() if settings.GAZETTEER_FULLTEXTSEARCH else Q(place_name__istartswith=place_name)
    if layers:
        criteria =  criteria & Q(layer_name__in=layers)

    if start_date:
        start_date = parse_julian_date(start_date)
        print("START DATE: %s" % start_date)

    if end_date:
        end_date = parse_julian_date(end_date)
        print("END DATE: %s" % end_date)

    if start_date and end_date:
        print ("BOTH DATES")
        #Return all placenames that ended after the start date or started before the end date
        criteria = criteria & (Q(julian_end__gte=start_date) &  Q(julian_start__lte=end_date) |\
                               (Q(julian_start__isnull=True) & Q(julian_end__gte=start_date)) |\
                               (Q(julian_end__isnull=True) &Q(julian_start__lte=end_date)) |\
                               (Q(julian_start__isnull=True) & Q(julian_end__isnull=True)))



    elif start_date:
        print ("START DATE ONLY")
        #Return all placenames that existed on this date or afterward
        #End_date >= the specified start date or start_date <= the specified date or both are null
        criteria = criteria & ((Q(julian_end__gte=start_date)) |\
                               (Q(julian_end__isnull=True) & Q(julian_start__lte=start_date)) |\
                               (Q(julian_start__isnull=True) & Q(julian_end__gte=start_date)) |\
                               (Q(julian_start__isnull=True) & Q(julian_end__isnull=True)))

    elif end_date:
        print ("END DATE ONLY")
        #Return all placenames that existed on this date or before
        #End_date >= the specified end date or start_date <= the specified date or both are null
        criteria = criteria & ((Q(julian_start__lte=end_date)) |\
                               (Q(julian_start__isnull=True) & Q(julian_end__gte=end_date)) |\
                               (Q(julian_end__isnull=True) & Q(julian_start__lte=end_date)) |\
                               (Q(julian_start__isnull=True) & Q(julian_end__isnull=True)))

    if project:
        criteria = criteria & Q(project__exact=project)
    if user:
        criteria = criteria & Q(username__exact=user)

    matchingEntries=(GazetteerEntry.objects.extra(
        where=['placename_tsv @@ to_tsquery(%s)'],
        params=[re.sub("\s+"," & ",place_name.strip()) + ":*"]).filter(criteria))[:500] \
        if settings.GAZETTEER_FULLTEXTSEARCH else GazetteerEntry.objects.filter(criteria)
    posts = []
    for entry in matchingEntries:
        posts.append({'placename': entry.place_name, 'coordinates': (entry.latitude, entry.longitude),
            'source': formatSourceLink(entry.layer_name), 'start_date': entry.start_date, 'end_date': entry.end_date,
            'gazetteer_id': entry.id})
    return posts


def delete_from_gazetteer(layer_name):
    """
    Delete all placenames for a layer
    """
    GazetteerEntry.objects.filter(layer_name__exact=layer_name).delete()


def add_to_gazetteer(layer_name, name_attributes, start_attribute=None,
                     end_attribute=None, project=None, user=None):
    """
    Add placenames from a WorldMap layer into the gazetteer.
    layer_name: Name of the layer
    name_attributes: array of layer attribute names to be added as source of placenames
    start_attribute: layer attribute to be used as start date
    end_attribute: layer attribute to be used as end date
    project: Name of project that layer will be associated with
    """

    def get_date_format(date_attribute):
        field_name = "l.\"" + date_attribute.attribute + "\""
        date_format = []
        if "xsd:date" not in date_attribute.attribute_type and date_attribute.date_format is not None:
            # This could be in any of multiple formats, and postgresql needs a format pattern to convert it.
            # User should supply this format when adding the layer attribute to the gazetteer
            date_format.append(
                "TO_CHAR(TO_DATE(CAST({name} AS TEXT), '{format}'), 'YYYY-MM-DD BC')".format(
                    name=field_name, format=date_attribute.date_format)
            )
            date_format.append(
                "CAST(TO_CHAR(TO_DATE(CAST({name} AS TEXT), '{format}'), 'J') AS integer)".format(
                    name=field_name, format=date_attribute.date_format)
                )
        elif "xsd:date" in date_attribute.attribute_type:
            # It's a date, convert to string
            date_format.append("TO_CHAR({}, 'YYYY-MM-DD BC')".format(field_name))
            date_format.append("CAST(TO_CHAR({}, 'J') AS integer)".format(field_name))
        elif not "xsd:date" in start_attribute_obj.attribute_type:
            # It's not a date, it's not an int, and no format was specified if it's a string - so don't use it
            date_format = [None, None]
        return date_format

    def get_metadata_format(metadata_date):
        date_format= []
        date_format.append(
            "TO_CHAR(TO_DATE(CAST('{}' AS TEXT), 'YYYY-MM-DD BC'), 'YYYY-MM-DD BC')".format(
            metadata_date))
        date_format.append(
            "CAST(TO_CHAR(TO_DATE(CAST('{}' AS TEXT), 'YYYY-MM-DD BC'), 'J') AS integer)".format(
                metadata_date))
        return date_format

    layer = get_object_or_404(Layer, name=layer_name)
    layer_type, geocolumn, projection = get_geometry_type(layer)

    namelist = "'" + "','".join(name_attributes) + "'"

    """
    Delete layer placenames where the FID is no longer in the original table or the layer_attribute is not in the list of name attributes.
    """

    conn = getConnection(layer.store)
    cur = conn.cursor()
    cur.execute("SELECT string_agg(fid::text, ',') as fids_list from %s;" % layer.name)
    fids = cur.fetchone()[0]

    delete_query = "DELETE FROM " + GAZETTEER_TABLE + " WHERE layer_name = '" + str(
        layer.name) + "' AND (feature_fid NOT IN (" + fids + ") OR layer_attribute NOT IN (" + namelist + "))"

    updateQueries = []
    insertQueries = []

    geom_query = "l." + geocolumn

    if projection != "4326":
        geom_query = "ST_Transform(" + geom_query + ",4326)"

    coord_query = geom_query
    if "POINT" not in layer_type:
        coord_query = "ST_Centroid(" + geom_query + ")"

    start_format, julian_start = None, None
    if start_attribute is not None:
        start_attribute_obj = get_object_or_404(LayerAttribute, layer=layer, attribute=start_attribute)
        start_dates = get_date_format(start_attribute_obj)
        start_format = start_dates[0]
        julian_start = start_dates[1]
    elif layer.temporal_extent_start:
        start_format, julian_start = get_metadata_format(layer.temporal_extent_start)

    end_format, julian_end = None, None
    if end_attribute is not None:
        end_attribute_obj = get_object_or_404(LayerAttribute, layer=layer, attribute=end_attribute)
        end_dates = get_date_format(end_attribute_obj)
        end_format = end_dates[0]
        julian_end = end_dates[1]
    elif layer.temporal_extent_end:
        end_format, julian_end = get_metadata_format(layer.temporal_extent_end)

    username = ("'%s'" % user) if user else 'NULL'

    updateTemplate = """
    UPDATE {table} SET layer_attribute = '{attribute}', feature = {geom},
    feature_type = '{type}', place_name = l."{attribute}", username = {username},
    start_date={sdate}, end_date = {edate},
    julian_start = {sjulian}, julian_end={ejulian}, project='{project}',
    longitude = ST_X({coord}), latitude = ST_Y({coord})
    FROM
    (select * from dblink('dbname={store}', 'select fid, {geocolumn}, "{attribute}" from {layer};') as lt
    (fid integer, {geocolumn} geometry, "{attribute}" {attribute_type})) as l
    WHERE layer_name = '{layer}' AND feature_fid = l.fid
    AND layer_attribute = '{attribute}' and l."{attribute}" is not NULL;
    """

    insertTemplate = """
    INSERT INTO {table} (layer_name, layer_attribute, feature_type, feature_fid,
    place_name, start_date, end_date, julian_start, julian_end, project,
    feature, longitude, latitude, username)
    (SELECT '{layer}' as layer_name, '{attribute}' as layer_attribute,
    '{type}' as feature_type, fid as feature_fid, "{attribute}" as place_name,
    {sdate} as start_date, {edate} as end_date, {sjulian} as
    julian_start, {ejulian} as julian_end, '{project}' as project, {geom} as
    feature, ST_X({coord}), ST_Y({coord}), {username}
    FROM
    (select * from dblink('dbname={store}', 'select fid, {geocolumn}, "{attribute}" from {layer};') as lt
    (fid integer, {geocolumn} geometry, "{attribute}" {attribute_type})) as l
    WHERE l."{attribute}" IS NOT NULL AND fid NOT IN
    (SELECT feature_fid FROM {table} WHERE layer_name = '{layer}' AND
    layer_attribute = '{attribute}'))
    """

    for name in name_attributes:
        attribute = get_object_or_404(LayerAttribute, layer=layer, attribute=name)

        # detect column type, needed by dblink
        cur = conn.cursor(layer.store)
        cur.execute("select data_type from information_schema.columns where table_name = '%s' and column_name = '%s';" % (layer_name, name))
        attribute_type = cur.fetchone()[0]
        cur.close()

        """
        Update layer placenames where placename FID = layer FID
        and placename layer attribute = name attribute
        """

        updateQuery =updateTemplate.format(
            table=GAZETTEER_TABLE,
            attribute=attribute.attribute,
            geom=geom_query,
            username=username,
            type=layer_type,
            sdate=(start_format if start_format else "NULL"),
            edate=(end_format if end_format else "NULL"),
            sjulian=(julian_start if julian_start else "NULL"),
            ejulian=(julian_end if julian_end else "NULL"),
            project=project,
            coord=coord_query,
            layer=layer_name,
            store=layer.store,
            geocolumn=geocolumn,
            attribute_type=attribute_type,
            )
        updateQueries.append(updateQuery)

        """
        Insert any new placenames
        """
        insertQuery = insertTemplate.format(
            table=GAZETTEER_TABLE,
            attribute=attribute.attribute,
            geom=geom_query,
            username=username,
            type=layer_type,
            sdate=start_format.replace("l.", "") if start_format else 'NULL',
            edate=end_format.replace("l.", "") if end_format else 'NULL',
            sjulian=julian_start if julian_start else "NULL",
            ejulian=julian_end if julian_end else "NULL",
            project=project,
            coord=coord_query,
            layer=layer_name,
            store=layer.store,
            geocolumn=geocolumn,
            attribute_type=attribute_type,)
        insertQueries.append(insertQuery)

    conn = getConnection()

    try:
        cur = conn.cursor()
        cur.execute(delete_query)
        logger.info(delete_query)
        for updateQuery in updateQueries:
            cur.execute(updateQuery)
            logger.info(updateQuery)
        for insertQuery in insertQueries:
            cur.execute(insertQuery)
            logger.info(insertQuery)
        conn.commit()
        cur.close()
        return "Done"
    except Exception, e:
        logger.error("Error retrieving type for PostGIS table %s:%s", layer_name, str(e))
        raise
    finally:
        conn.close()




def getExternalServiceResults(place_name, services):
    results = []
    for service in services.split(',', ):
        if service == "google":
            google = getGoogleResults(place_name)
            results.extend(google)
        elif service == "nominatim":
            nominatim = getNominatimResults(place_name)
            results.extend(nominatim)
        elif service == "geonames":
            geonames = getGeonamesResults(place_name)
            results.extend(geonames)
    return results


def getGoogleResults(place_name):
    g = geocoders.GoogleV3(client_id=settings.GOOGLE_API_KEY,
        secret_key=settings.GOOGLE_SECRET_KEY) if settings.GOOGLE_SECRET_KEY is not None else geocoders.GoogleV3()
    try:
        results = g.geocode(place_name, exactly_one=False)
        formatted_results = []
        for result in results:
            formatted_results.append(formatExternalGeocode('Google', result))
        return formatted_results
    except Exception:
        return []


def getNominatimResults(place_name):
    g = geocoders.Nominatim()
    try:
        results = g.geocode(place_name, False,timeout=5)
        formatted_results = []
        for result in results:
            formatted_results.append(formatExternalGeocode('Nominatim', result))
        return formatted_results
    except:
        return []

def getConnection(layer_store=None):
    dbname = settings.DATABASES[settings.GAZETTEER_DB_ALIAS]['NAME']
    if layer_store:
        dbname = layer_store
    return psycopg2.connect(
        "dbname='" + dbname + "' user='" + \
        settings.DATABASES[settings.GAZETTEER_DB_ALIAS]['USER'] + "'  password='" + \
        settings.DATABASES[settings.GAZETTEER_DB_ALIAS]['PASSWORD'] + "' port=" + \
        settings.DATABASES[settings.GAZETTEER_DB_ALIAS]['PORT'] + " host='" + \
        settings.DATABASES[settings.GAZETTEER_DB_ALIAS]['HOST'] + "'")

def getGeonamesResults(place_name):
    g = geocoders.GeoNames(username=settings.GEONAMES_USER)
    try:
        results = g.geocode(place_name, False)
        formatted_results = []
        for result in results:
            formatted_results.append(formatExternalGeocode('Geonames', result))
        return formatted_results
    except:
        return []


def formatExternalGeocode(geocoder, geocodeResult):
    return {'placename': geocodeResult[0], 'coordinates': geocodeResult[1], 'source': geocoder, 'start_date': 'N/A', \
            'end_date': 'N/A', 'gazetteer_id': 'N/A'}
