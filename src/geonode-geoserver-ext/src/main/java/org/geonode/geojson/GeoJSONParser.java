package org.geonode.geojson;

import static org.geonode.geojson.GeoJSONObjectType.GEOMETRYCOLLECTION;

import java.util.ArrayList;
import java.util.Iterator;

import net.sf.json.JSONArray;
import net.sf.json.JSONException;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

import org.geotools.feature.FeatureCollection;
import org.geotools.feature.FeatureCollections;
import org.geotools.feature.SchemaException;
import org.geotools.feature.simple.SimpleFeatureBuilder;
import org.geotools.feature.simple.SimpleFeatureTypeBuilder;
import org.opengis.feature.simple.SimpleFeature;
import org.opengis.feature.simple.SimpleFeatureType;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryCollection;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.LineString;
import com.vividsolutions.jts.geom.LinearRing;
import com.vividsolutions.jts.geom.MultiLineString;
import com.vividsolutions.jts.geom.MultiPoint;
import com.vividsolutions.jts.geom.MultiPolygon;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.Polygon;

/**
 * This class is a (complementary) companion class to {@link GeoJSONSerializer}.
 * 
 * @author originally written by Nicholas Bergson-Shilcock at the The Open Planning Project and
 *         adapted by Gabriel Roldan afterwards
 * @version $Id$
 */
public class GeoJSONParser {
    private GeoJSONConfig config;

    public GeoJSONParser(final GeoJSONConfig config) {
        this.config = config;
    }

    private static GeometryFactory gf = new GeometryFactory();

    // TODO: add support for CRS
    // TODO: add support for bbox

    /**
     * Converts any GeoJSON object into a Geometry, Feature, or FeatureCollection object.
     * 
     * @param jsonStr
     *            - The JSON object (as a String) to convert
     * @return The Geometry, Feature, or FeatureCollection with the new geometry/feature
     * @throws JSONException
     *             if anything goes wrong
     */
    public static Object parse(String jsonStr) throws JSONException {
        return parse(jsonStr, null);
    }

    /**
     * Converts any GeoJSON object into a Geometry, Feature, or FeatureCollection object.
     * 
     * @param obj
     *            - The JSONObject to convert
     * @return The Geometry, Feature, or FeatureCollection with the new geometry/feature
     * @throws JSONException
     *             if anything goes wrong
     */
    public static Object parse(JSONObject obj) throws JSONException {
        return parse(obj, null);
    }

    /**
     * Converts any GeoJSON object into a Geometry, Feature, or FeatureCollection object.
     * 
     * @param jsonStr
     *            - The JSON object (as a String) to convert
     * @param featureType
     *            - The FeatureType to use when creating the Feature objects
     * @return The Geometry, Feature, or FeatureCollection with the new geometry/feature
     * @throws JSONException
     *             if anything goes wrong
     */
    public static Object parse(String jsonStr, SimpleFeatureType featureType) throws JSONException {
        JSONObject obj = (JSONObject) JSONSerializer.toJSON(jsonStr);

        return parse(obj, featureType);
    }

    /**
     * Converts any GeoJSON object into a Geometry, Feature, or FeatureCollection object.
     * 
     * @param obj
     *            - The JSONObject to convert
     * @param featureType
     *            - The FeatureType to use when creating the Feature objects
     * @return The Geometry, Feature, or FeatureCollection with the new geometry/feature
     * @throws JSONException
     *             if anything goes wrong
     */
    public static Object parse(JSONObject obj, SimpleFeatureType featureType) throws JSONException {
        if (!obj.containsKey("type")) {
            throw new JSONException("Missing required attribute 'type'");
        }

        final String typeStr = obj.getString("type");
        final GeoJSONObjectType objType = GeoJSONObjectType.fromJSONTypeName(typeStr);

        switch (objType) {
        case FEATURE:
            return parseFeature(obj, featureType);

        case FEATURECOLLECTION:
            return parseFeatureCollection(obj, featureType);

        default:
            return parseGeometry(obj);
        }
    }

    /**
     * Generates a new FeatureType based on the passed in Feature. If the GeoJSON object passed is a
     * FeatureCollection, the first feature in the "features" property is used for the schema.
     * 
     * @param jsonStr
     *            - the JSON object to grab the prototypical feature from
     * @return The new FeatureType object
     * @throws SchemaException
     * @throws JSONException
     */
    public static SimpleFeatureType getFirstFeatureType(String jsonStr) throws JSONException {
        JSONObject jsonObj = (JSONObject) JSONSerializer.toJSON(jsonStr);

        return getFirstFeatureType(jsonObj);
    }

    /**
     * Generates a new FeatureType based on the passed in Feature. If the GeoJSON object passed is a
     * FeatureCollection, the first feature in the "features" property is used for the schema.
     * 
     * @param obj
     *            - the JSON object to grab the prototypical feature from
     * @return The new FeatureType object
     * @throws SchemaException
     * @throws JSONException
     */
    public static SimpleFeatureType getFirstFeatureType(JSONObject obj) throws JSONException {
        if (!obj.containsKey("type")) {
            throw new JSONException("Missing required attribute 'type'");
        }

        final String typeStr = obj.getString("type");
        final GeoJSONObjectType objType = GeoJSONObjectType.fromJSONTypeName(typeStr);

        JSONObject prototype = null;
        switch (objType) {
        case FEATURE:
            prototype = obj;

            break;

        case FEATURECOLLECTION:

            if (!obj.containsKey("features")) {
                throw new JSONException("Missing required attribute 'features'");
            }

            JSONArray array = obj.getJSONArray("features");
            if (array.size() == 0) {
                throw new JSONException(
                        "No features present in the FeatureCollection, can't infer FeatureType");
            }
            prototype = array.getJSONObject(0);

            break;

        default:
            throw new JSONException("Object must be feature or feature collection");
        }

        return createType(prototype);
    }

    /**
     * Actually creates a new FeatureType based on the object passed in.
     * 
     * @param prototype
     *            The GeoJSON object to use as the basis for the schema
     * @return The new FeatureType object
     * @throws SchemaException
     */
    @SuppressWarnings("unchecked")
    private static SimpleFeatureType createType(JSONObject prototype) throws JSONException {
        SimpleFeatureTypeBuilder typeBuilder = new SimpleFeatureTypeBuilder();
        typeBuilder.setName("none");

        String name = "";
        Class<?> binding;

        for (Iterator<String> keys = prototype.keys(); keys.hasNext();) {
            name = keys.next().toLowerCase();

            if (name.equals("geometry")) {
                binding = Geometry.class;
            } else if (name.equals("properties")) {
                binding = Object.class;
            } else {
                binding = String.class;
            }

            // attributeType = AttributeTypeFactory.newAttributeType(name, typeClass);

            if (!name.equals("id") && !name.equals("type")) {
                // typeBuilder.addType(attributeType);
                typeBuilder.add(name, binding);
            }
        }

        return typeBuilder.buildFeatureType();
    }

    private static SimpleFeature parseFeature(JSONObject obj, SimpleFeatureType type)
            throws JSONException {
        // TODO: This method uses featureType.create() to create new features, which
        // seems to be the old way of doing things. What's the proper new way?
        if (!obj.containsKey("geometry") || !obj.containsKey("properties")) {
            throw new JSONException("Invalid GeoJSON feature object");
        }

        SimpleFeatureType featureType = type;

        // Create feature type if none is provided
        // Note that this is rather inefficient if all the features are of the
        // same type, as the FeatureType will be recreated for each feature.
        if (type == null) {
            featureType = getFirstFeatureType(obj);
        }

        // Construct a new array with the attribute values for this feature,
        // skipping the 'type' attribute and the 'id' attribute if it exists.
        String key;
        ArrayList values = new ArrayList();

        for (Iterator iter = obj.keys(); iter.hasNext();) {
            key = (String) iter.next();

            if (key.equals("geometry")) {
                values.add(parseGeometry(obj.getJSONObject(key)));
            } else if (!key.equals("type") && !key.equals("id")) {
                values.add(obj.get(key));
            }
        }

        SimpleFeatureBuilder sfb = new SimpleFeatureBuilder(featureType);

        // Use id if it exists, otherwise generate one...
        String fid = null;
        if (obj.containsKey("id")) {
            fid = obj.getString("id");
        }
        SimpleFeature feature = sfb.buildFeature(fid, values.toArray());
        return feature;
    }

    private static FeatureCollection parseFeatureCollection(JSONObject obj, SimpleFeatureType type)
            throws JSONException {

        if (!obj.containsKey("features")) {
            throw new JSONException("Missing required attribute 'features'");
        }

        FeatureCollection featureCollection = FeatureCollections.newCollection();
        JSONArray features = obj.getJSONArray("features");

        for (int i = 0; i < features.size(); i++)
            featureCollection.add(parseFeature(features.getJSONObject(i), type));

        return featureCollection;
    }

    private static Geometry parseGeometry(final JSONObject obj) throws JSONException {
        if (!obj.containsKey("type")) {
            throw new JSONException("Missing required attribute 'type'");
        }

        final String typeStr = obj.getString("type");
        final GeoJSONObjectType geomType = GeoJSONObjectType.fromJSONTypeName(typeStr);

        if (geomType == GEOMETRYCOLLECTION) {
            return parseGeometryCollection(obj);
        } else {
            if (!obj.containsKey("coordinates")) {
                throw new JSONException("Missing required attribute 'coordinates'");
            }

            JSONArray coords = obj.getJSONArray("coordinates");

            switch (geomType) {
            case POINT:
                return parsePoint(coords);

            case MULTIPOINT:
                return parseMultiPoint(coords);

            case LINESTRING:
                return parseLineString(coords);

            case MULTILINESTRING:
                return parseMultiLineString(coords);

            case POLYGON:
                return parsePolygon(coords);

            case MULTIPOLYGON:
                return parseMultiPolygon(coords);

            default:
                throw new JSONException("Invalid geometry type");
            }
        }
    }

    private static Point parsePoint(final JSONArray xy) {
        Coordinate coord = new Coordinate(xy.getDouble(0), xy.getDouble(1));

        return gf.createPoint(coord);
    }

    private static LineString parseLineString(JSONArray points) {
        JSONArray xy;
        Coordinate[] coords = new Coordinate[points.size()];

        for (int i = 0; i < coords.length; i++) {
            xy = points.getJSONArray(i);
            coords[i] = new Coordinate(xy.getDouble(0), xy.getDouble(1));
        }

        return gf.createLineString(coords);
    }

    private static Polygon parsePolygon(JSONArray vals) {
        JSONArray innerPoints;
        JSONArray xy;
        JSONArray outlinePoints = vals.getJSONArray(0);

        // get the outline of the polygon
        Coordinate[] outlineCoords = new Coordinate[outlinePoints.size()];

        for (int i = 0; i < outlinePoints.size(); i++) {
            xy = outlinePoints.getJSONArray(i);
            outlineCoords[i] = new Coordinate(xy.getDouble(0), xy.getDouble(1));
        }

        LinearRing outer = gf.createLinearRing(outlineCoords);

        // get the holes (if any)
        LinearRing[] inner = null;

        if (vals.size() > 1) {
            inner = new LinearRing[vals.size() - 1];

            for (int i = 1; i < vals.size(); i++) {
                innerPoints = vals.getJSONArray(i);

                Coordinate[] hole = new Coordinate[innerPoints.size()];

                for (int j = 0; j < innerPoints.size(); j++) {
                    xy = innerPoints.getJSONArray(j);
                    hole[j] = new Coordinate(xy.getDouble(0), xy.getDouble(1));
                }

                inner[i] = gf.createLinearRing(hole);
            }
        }

        return gf.createPolygon(outer, inner);
    }

    private static MultiPoint parseMultiPoint(JSONArray vals) {
        Point[] points = new Point[vals.size()];

        for (int i = 0; i < vals.size(); i++)
            points[i] = parsePoint(vals.getJSONArray(i));

        return gf.createMultiPoint(points);
    }

    private static MultiLineString parseMultiLineString(JSONArray vals) {
        LineString[] lines = new LineString[vals.size()];

        for (int i = 0; i < vals.size(); i++)
            lines[i] = parseLineString(vals.getJSONArray(i));

        return gf.createMultiLineString(lines);
    }

    private static MultiPolygon parseMultiPolygon(JSONArray vals) {
        Polygon[] polys = new Polygon[vals.size()];

        for (int i = 0; i < vals.size(); i++) {
            polys[i] = parsePolygon(vals.getJSONArray(i));
        }

        return gf.createMultiPolygon(polys);
    }

    protected static GeometryCollection parseGeometryCollection(JSONObject obj)
            throws JSONException {
        if (!obj.containsKey("geometries")) {
            throw new JSONException("Missing required attribute 'geometries'");
        }

        JSONArray geometries = obj.getJSONArray("geometries");
        Geometry[] geomObjs = new Geometry[geometries.size()];

        for (int i = 0; i < geometries.size(); i++)
            geomObjs[i] = parseGeometry(geometries.getJSONObject(i));

        return gf.createGeometryCollection(geomObjs);
    }

}
