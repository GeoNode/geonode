import logging
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
#from geonode.gazetteer.models import GazetteerEntry
#from psycopg2 import extras
from geonode.gazetteer.models import GazetteerEntry
from geopy import geocoders
from django.conf import settings
import psycopg2
from django.db.models import Q
from geonode.maps.models import Layer, LayerAttribute, MapLayer, Map
from datautil.date import DateutilDateParser

GAZETTEER_TABLE = 'gazetteer_gazetteerentry'

__author__ = 'mbertrand'

logger = logging.getLogger("geonode.gazetteer.utils")

'''
ALTER TABLE gazetteer_placename ADD COLUMN text_search tsvector;
UPDATE gazetteer_placename SET text_search =
     to_tsvector('english', coalesce(place_name,''));
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
  ON gazetteer_placename FOR EACH ROW EXECUTE PROCEDURE
  tsvector_update_trigger(text_search, 'pg_catalog.english', place_name);
'''

def get_geometry_type(layer_name):
    """
    Return the geometry type (POINT, POLYGON etc), geometry column name, and projection of a layer
    """

    conn = psycopg2.connect(
        "dbname='" + settings.DB_DATASTORE_DATABASE + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")
    try:
        cur = conn.cursor()
        cur.execute("select type, f_geometry_column, srid from geometry_columns where f_table_name = '%s'" % layer_name)
        result = cur.fetchone()
        #print result
        return result
    except Exception, e:
        logger.error("Error retrieving type for PostGIS table %s:%s", layer_name, str(e))
        raise
    finally:
        conn.close()


def getGazetteerEntry(id):

    #sql_query = "SELECT  place_name, layer_name, latitude, longitude, id from gazetteer_placename WHERE id = %d" % id
    #conn = psycopg2.connect(
    #    "dbname='" + settings.DB_DATASTORE_DATABASE + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")
    try:
        #cur = conn.cursor()
        #cur.execute(sql_query)
        #results = cur.fetchall()

        results = GazetteerEntry.objects.filter(id__exact=id)

        posts = []
        for entry in results:
            #(result[0] + ':' + str(result[1]) + ':' + str(result[2]) + ':' + str(result[3]))
            posts.append({'placename': entry.place_name, 'coordinates': (entry.longitude, entry.latitude),
                          'source': formatSourceLink(entry.layer_name), 'id': entry.id})
        return posts
    except Exception, e:
        logger.error("Error retrieving results for gazetteer by id %d:%s", id, str(e))
        raise
    finally:
        conn.close()


def formatSourceLink(layer_name):
    layer = Layer.objects.get(name=layer_name)
    return "<a href='{0}data/{1}' target='_blank'>{2}</a>".format(settings.SITEURL, layer.typename, layer.name)


def getGazetteerResults(place_name, map=None, layer=None, start_date=None, end_date=None, project=None):
    """
    Return placenames from gazetteer that match certain filters:
        place_name: text to do a LIKE search for
        map: search all layers that are present in this map (map id)
        layer: search only this layer (layer name)
        start_date: return only matches with a start date >= this value
        end_date: return only matches with an end date <= this value
        project: only return matches within the specified project
    """

    parser = DateutilDateParser()


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
## Unfortunately, python datetime can't handle dates < 1 AD (WTF!?)so
## going back to using direct SQL queries for now

#    criteria = Q(place_name__istartswith=place_name)
#
#    if layers:
#        criteria = criteria & Q(layer_name__in=layers)
#
#    if start_date:
#        start_date = parser.parse(start_date)
#        #Start_date is >= the specified start date or no start date
#        criteria = criteria & (Q(start_date__gte=start_date) | Q(start_date__isnull=True))
#        # AND End_date is >= the specified start date or no end date
#        criteria = criteria & (Q(end_date__gte=start_date) | Q(end_date__isnull=True))
#
#    if end_date:
#        end_date = parser.parse(end_date)
#        #End_date is <= the specified end date or no end date
#        criteria = criteria & (Q(end_date__lte=end_date) | Q(end_date__isnull=True))
#        # AND start_date <= specified end date or no start date
#        criteria = criteria & (Q(start_date__lte=end_date) | Q(start_date__isnull=True))
#
#    if project:
#        criteria = criteria & Q(project__exact=project)
#
#    matchingEntries=GazetteerEntry.objects.filter(criteria)
#
#    posts = []
#
#    for entry in matchingEntries:
#        #print(result[0] + ':' + str(result[1]) + ':' + str(result[2]) + ':' + str(result[3]))
#        posts.append({'placename': entry.place_name, 'coordinates': (entry.latitude, entry.longitude),
#            'source': formatSourceLink(entry.layer_name), 'start_date': entry.start_date, 'end_date': entry.end_date,
#            'gazetteer_id': entry.id})
#    return posts
#
#
#    return posts



    #"select ts_headline(place_name, to_tsquery('" + place_name + "')), layer_name, latitude, longitude, start_date, end_date, id from gazetteer_placename, to_tsquery('" + place_name + "') query where query @@ text_search"

    sql_query = "SELECT place_name, layer_name, latitude, longitude, TO_CHAR(start_date,'YYYY-MM-DD BC'), TO_CHAR(end_date,'YYYY-MM-DD BC'), id from gazetteer_gazetteerentry WHERE place_name ILIKE '" + place_name + "\%'"
    if layers:
        layers_str = "'" + "','".join(layers) + "'"
        sql_query += " AND layer_name in (" + layers_str + ")"

    if start_date: #Select records whose start/end_date is >= the specified start date
        sql_query += " AND (end_date >= CAST('" + start_date + "' as date) OR "
        sql_query += "(start_date is null or start_date >= CAST('" + start_date + "' as date)))"

    if end_date: #Select records whose start date is <= the specified end date (or no start date)
        sql_query += " AND ((end_date <= CAST('" + end_date + "' as date) OR end_date is null) AND"
        sql_query += " (start_date <= CAST('" + end_date + "' as date) OR start_date is null)"

    if project:
        sql_query += " AND project = '" + project + "'"

    #print("SQL QUERY IS: %s", sql_query)

    conn = psycopg2.connect(
        "dbname='" + settings.DB_DATASTORE_DATABASE + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()

        posts = []
        for result in results:
            #print(result[0] + ':' + str(result[1]) + ':' + str(result[2]) + ':' + str(result[3]))
            posts.append({'placename': result[0], 'coordinates': (result[2], result[3]),
                          'source': formatSourceLink(result[1]), 'start_date': result[4], 'end_date': result[5],
                          'gazetteer_id': result[6]})
            #posts.append({"type": "Feature", "geometry": {"type": "Point", "coordinates":[result[2], result[3]]}, "properties": {'placename': result[0], 'source': result[1], 'start_date': result[4], 'end_date': result[5], 'gazetteer_id': result[6]}})
        return posts
    except Exception, e:
        logger.error("Error retrieving type for PostGIS table %s:%s", layer, str(e))
        raise
    finally:
        conn.close()


def delete_from_gazetteer(layer_name):
    """
    Delete all placenames for a layer
    """

#    If this were to use a django objemt model....
#    GazetteerEntry.objects.filter(layer_name__exact=layer_name).delete()

    delete_query = "DELETE FROM " + GAZETTEER_TABLE + " WHERE layer_name = '%s'" % layer_name
    print delete_query
    conn = psycopg2.connect(
        "dbname='" + settings.DB_DATASTORE_DATABASE + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")
    try:
        cur = conn.cursor()
        cur.execute(delete_query)
    except Exception, e:
        logger.error("Error deleting %s from gazetteer: %s", layer_name, str(e))
        raise
    finally:
        conn.close()


def add_to_gazetteer(layer_name, name_attributes, start_attribute=None, end_attribute=None, project=None):
    """
    Add placenames from a WorldMap layer into the gazetteer.
    layer_name: Name of the layer
    name_attributes: array of layer attribute names to be added as source of placenames
    start_attribute: layer attribute to be used as start date
    end_attribute: layer attribute to be used as end date
    project: Name of project that layer will be associated with
    """

    def getDateFormat(date_attribute):
        date_format = "l.\"" + date_attribute.attribute + "\""
        if "xsd:date" not in date_attribute.attribute_type and date_attribute.date_format is not None:
            #This could be in any of multiple formats, and postgresql needs a format pattern to convert it.
            #User should supply this format when adding the layer attribute to the gazetteer
            date_format = "TO_DATE(CAST(" + date_format + " AS TEXT), '" + date_attribute.date_format + "')"
        elif not "xsd:date" in start_attribute_obj.attribute_type:
            #It's not a date, it's not an int, and no format was specified if it's a string - so don't use it
            date_format = None
        return date_format

    layer = get_object_or_404(Layer, name=layer_name)
    layer_type, geocolumn, projection = get_geometry_type(layer_name)

    namelist = "'" + "','".join(name_attributes) + "'"

    """
    Delete layer placenames where the FID is no longer in the original table or the layer_attribute is not in the list of name attributes.
    """
    delete_query = "DELETE FROM " + GAZETTEER_TABLE + " WHERE layer_name = '" + str(
        layer.name) + "' AND (feature_fid NOT IN (SELECT fid from \"" + layer.name + "\") OR layer_attribute NOT IN (" + namelist + "))"
    #print delete_query

    updateQueries = []
    insertQueries = []

    geom_query = "l." + geocolumn

    if projection != "4326":
        geom_query = "ST_Transform(" + geom_query + ",4326)"

    coord_query = geom_query
    if "POINT" not in layer_type:
        coord_query = "ST_Centroid(" + geom_query + ")"

    start_format = None
    if start_attribute is not None:
        start_attribute_obj = get_object_or_404(LayerAttribute, layer=layer, attribute=start_attribute)
        start_format = getDateFormat(start_attribute_obj)

    end_format = None
    if end_attribute is not None:
        end_attribute_obj = get_object_or_404(LayerAttribute, layer=layer, attribute=end_attribute)
        end_format = getDateFormat(end_attribute_obj)

    for name in name_attributes:
        #print("Attribute:" + name + " for " + layer.name)
        attribute = get_object_or_404(LayerAttribute, layer=layer, attribute=name)
        """
        Update layer placenames where placename FID = layer FID and placename layer attribute = name attribute
        """
        updateQueries.append("UPDATE " + GAZETTEER_TABLE + " SET layer_attribute = '" + str(
            attribute.attribute) + "', feature = " + geom_query + ", feature_type = '" + layer_type +\
                             "', place_name = l.\"" + attribute.attribute + "\"" +
        ", start_date = " + (start_format if start_format else "null") +\
                             ", end_date = " + (end_format if end_format else "null") +\
                             ", project = " + ("'" + project + "'" if project else "null") +\
                             ", longitude = ST_X(" + coord_query + "), latitude = ST_Y(" + coord_query + ")" +\
                             " FROM \"" + layer_name + "\" as l WHERE layer_name = '" + layer_name + "' AND" +\
                             " feature_fid = l.fid AND layer_attribute = '" + attribute.attribute + "' and l.\"" +\
                             attribute.attribute + "\" is not null")
        """
        Insert any new placenames
        """
        insertQueries.append(
            "INSERT INTO " + GAZETTEER_TABLE + " (layer_name, layer_attribute, feature_type, feature_fid, place_name, start_date, end_date, project, feature, longitude, latitude) (SELECT '" + str(
                    layer.name) + "' as layer_name,'" + str(
                    attribute.attribute) + "' as layer_attribute,'" + layer_type + "' as feature_type,fid as feature_fid,"\
                + "\"" + attribute.attribute + "\" as place_name," +\
                (start_format.replace("l.","") if start_format else 'null') + " as start_attribute," +\
                (end_format.replace("l.","") if end_format else 'null') + " as end_attribute," +\
                ("'" + project + "'" if project else 'null') + " as project" +\
                "," + geom_query + " as feature," +\
            "ST_X(" + coord_query + "), ST_Y(" + coord_query + ") from " + layer_name +\
            " as l WHERE  l.\"" + attribute.attribute + "\" is not null AND " +\
            "fid not in (SELECT feature_fid from " + GAZETTEER_TABLE + " where layer_name = '" + layer_name + "' and layer_attribute = '" + attribute.attribute + "'))")

    conn = psycopg2.connect(
        "dbname='" + settings.DB_DATASTORE_DATABASE + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")

    try:
        cur = conn.cursor()
        cur.execute(delete_query)
        logger.info(delete_query)
        for updateQuery in updateQueries:
            #print updateQuery
            cur.execute(updateQuery)
            logger.info(updateQuery)
        for insertQuery in insertQueries:
            #print insertQuery
            cur.execute(insertQuery)
            logger.info(insertQuery)
        conn.commit()
        cur.close()
        return "Done"
    except Exception, e:
        #print ("Error retrieving type for PostGIS table %s:%s", layer_name, str(e))
        logger.error("Error retrieving type for PostGIS table %s:%s", layer_name, str(e))
        raise
    finally:
        conn.close()


#def alternateUpdateGazetteer():
#    #If this were to use a django object model....
#    matchingEntries = GazetteerEntry.objects.filter(place_name__ilike(place_name))
#
#    if layers:
#        matchingEntries.filter(layer_name__in=layers)
#
#    if start_date: #Select records whose end_date is >= the specified start date (or no end date)
#        matchingEntries.filter(start_date__gte=start_date)
#
#    if end_date: #Select records whose start date is <= the specified end date (or no start date)
#        matchingEntries.filter(end_date__lte=start_date)
#
#    if project:
#        matchingEntries.filter(project__exact=project)
#
#    return matchingEntries

#def addGazetteerEntry(row):
#    entry,created = GazetteerEntry.objects.get_or_create(layer_name=row['layer_name'], layer_attribute=row['layer_attribute'],
#        feature_fid=row['feature_fid'], defaults={'feature_type':row['feature_type'],
#        'latitude':row['latitude'], 'longitude':row['longitude'], 'place_name':row['place_name'],
#         'project':row['project'], 'feature':GEOSGeometry(row['feature'])
#        })
#    try:
#        entry.save()
#    except Exception, e:
#        logger.error(str(e))




def getExternalServiceResults(place_name, services):
    results = []
    for service in services.split(',', ):
        if service == "google":
            #print("get Google")
            google = getGoogleResults(place_name)
            results.extend(google)
        elif service == "yahoo":
            #print("get Yahoo")
            yahoo = getYahooResults(place_name)
            results.extend(yahoo)
        elif service == "geonames":
            #print("get Geonames")
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


def getYahooResults(place_name):
    g = geocoders.Yahoo(settings.YAHOO_API_KEY)
    try:
        results = g.geocode(place_name, False)
        formatted_results = []
        for result in results:
            formatted_results.append(formatExternalGeocode('Yahoo', result))
        return formatted_results
    except:
        return []


def getGeonamesResults(place_name):
    g = geocoders.GeoNames()
    try:
        results = g.geocode(place_name, False)
        formatted_results = []
        for result in results:
            formatted_results.append(formatExternalGeocode('Geonames', result))
        return formatted_results
    except:
        return []


def formatExternalGeocode(geocoder, geocodeResult):
    return {'placename': geocodeResult[0], 'coordinates': geocodeResult[1], 'source': geocoder, 'start_date': 'N/A',
            'end_date': 'N/A', 'gazetteer_id': 'N/A'}
    #return {"type": "Feature", "geometry": {"type": "Point", "coordinates":geocodeResult[1]}, "properties": {'placename': geocodeResult[0], 'source': geocoder, 'start_date': 'N/A', 'end_date': 'N/A', 'gazetteer_id': 'N/A'}}