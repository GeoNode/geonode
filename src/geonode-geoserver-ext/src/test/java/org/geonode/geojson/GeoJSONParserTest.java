package org.geonode.geojson;

import static org.junit.Assert.assertTrue;

import java.io.StringWriter;

import net.sf.json.JSONException;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

import org.geotools.feature.SchemaException;
import org.geotools.feature.simple.SimpleFeatureBuilder;
import org.geotools.feature.simple.SimpleFeatureTypeBuilder;
import org.geotools.referencing.crs.DefaultGeographicCRS;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opengis.feature.IllegalAttributeException;
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

public class GeoJSONParserTest {

    private GeoJSONParser parser;

    /**
     * TODO: change this to a GeoTools config when the GeoJSONConfig interface is abstracted out
     */
    private GeoJSONConfig config = new GeoJSONConfig();

    @Before
    public void setUp() throws Exception {
        parser = new GeoJSONParser(config);
    }

    @After
    public void tearDown() throws Exception {
    }

    @Test
    public void testPoint() throws IllegalAttributeException, JSONException, SchemaException {
        GeometryFactory gf = new GeometryFactory();
        Coordinate coord = new Coordinate(120.0, 0.0);
        Point origPoint = gf.createPoint(coord);

        JSONObject jsonObj = createJSONObject(origPoint);

        Point newPoint = (Point) GeoJSONParser.parse(jsonObj);

        assertTrue(newPoint.equals(origPoint));
    }

    @Test
    public void testLineString() throws JSONException {
        GeometryFactory gf = new GeometryFactory();
        Coordinate[] coords = new Coordinate[4];
        coords[0] = new Coordinate(20.2, 10.1);
        coords[1] = new Coordinate(12.4, 1.0);
        coords[2] = new Coordinate(12.4, 5.5);
        coords[3] = new Coordinate(14, 42);

        LineString origLine = gf.createLineString(coords);

        JSONObject jsonObj = createJSONObject(origLine);

        LineString newLine = (LineString) GeoJSONParser.parse(jsonObj);

        assertTrue(newLine.equals(origLine));
    }

    @Test
    public void testPolygon() throws JSONException {
        GeometryFactory gf = new GeometryFactory();
        Coordinate[] coords = new Coordinate[4];
        coords[0] = new Coordinate(0.0, 0.1);
        coords[1] = new Coordinate(2.1, 0.12);
        coords[2] = new Coordinate(1.4, 1.0);
        coords[3] = new Coordinate(0.0, 0.1);

        LinearRing ring = gf.createLinearRing(coords);
        Polygon origPoly = gf.createPolygon(ring, null);

        JSONObject jsonObj = createJSONObject(origPoly);

        Polygon newPoly = (Polygon) GeoJSONParser.parse(jsonObj);

        assertTrue(newPoly.equals(origPoly));
    }

    @Test
    public void testMultiPoint() throws JSONException {
        GeometryFactory gf = new GeometryFactory();
        Coordinate[] coords = new Coordinate[3];
        coords[0] = new Coordinate(142, 142);
        coords[1] = new Coordinate(202.0, 128.0);
        coords[2] = new Coordinate(84.0, 8.0);

        MultiPoint origPoints = gf.createMultiPoint(coords);

        JSONObject jsonObj = createJSONObject(origPoints);

        MultiPoint newPoints = (MultiPoint) GeoJSONParser.parse(jsonObj);

        assertTrue(newPoints.equals(origPoints));
    }

    @Test
    public void testMultiLineString() throws JSONException {
        GeometryFactory gf = new GeometryFactory();
        LineString line1 = gf.createLineString(new Coordinate[] { new Coordinate(0, 0),
                new Coordinate(1, 2) });
        LineString line2 = gf.createLineString(new Coordinate[] { new Coordinate(3, 2),
                new Coordinate(4, 2) });
        MultiLineString origMLS = gf.createMultiLineString(new LineString[] { line1, line2 });

        JSONObject jsonObj = createJSONObject(origMLS);

        MultiLineString newMLS = (MultiLineString) GeoJSONParser.parse(jsonObj);

        assertTrue(newMLS.equals(origMLS));
    }

    @Test
    public void testMultiPolygon() throws JSONException {
        GeometryFactory gf = new GeometryFactory();
        LinearRing ring1 = gf.createLinearRing(new Coordinate[] { new Coordinate(0, 0),
                new Coordinate(1, 1), new Coordinate(1, 2), new Coordinate(0, 2),
                new Coordinate(0, 0) });
        LinearRing ring2 = gf.createLinearRing(new Coordinate[] { new Coordinate(10, 10),
                new Coordinate(10, 14), new Coordinate(5, 12), new Coordinate(10, 10) });
        Polygon poly1 = gf.createPolygon(ring1, null);
        Polygon poly2 = gf.createPolygon(ring2, null);
        MultiPolygon origMultiPoly = gf.createMultiPolygon(new Polygon[] { poly1, poly2 });

        JSONObject jsonObj = createJSONObject(origMultiPoly);

        MultiPolygon newMultiPoly = (MultiPolygon) GeoJSONParser.parse(jsonObj);

        assertTrue(newMultiPoly.equals(origMultiPoly));
    }

    @Test
    public void testGeometryCollection() throws JSONException {
        GeometryFactory gf = new GeometryFactory();
        Geometry[] geometries = new Geometry[3];
        geometries[0] = gf.createPoint(new Coordinate(1.0, 1.4));
        geometries[1] = gf.createLineString(new Coordinate[] { new Coordinate(32, 64),
                new Coordinate(192, 160) });
        geometries[2] = gf.createPoint(new Coordinate(2.0, 2.0));

        GeometryCollection origCollection = gf.createGeometryCollection(geometries);

        // JSONObject jsonObj = createJSONObject(origCollection);
        // TODO: For some reason GeoJSONBuilder dies on the above GeometryCollection
        // A hack to manually construct the JSON string
        String jsonStr = "{\"type\": \"GeometryCollection\", \"geometries\": "
                + "[ { \"type\": \"Point\", \"coordinates\": [1.0, 1.4] },"
                + "  { \"type\": \"LineString\", \"coordinates\": [ [32, 64], [192, 160] ]},"
                + "  { \"type\": \"Point\", \"coordinates\": [2.0, 2.0] },]}";

        JSONObject jsonObj = (JSONObject) JSONSerializer.toJSON(jsonStr);
        GeometryCollection newCollection = (GeometryCollection) GeoJSONParser.parse(jsonObj);

        if (origCollection.getNumGeometries() != newCollection.getNumGeometries()) {
            assertTrue(false);
        }

        for (int i = 0; i < origCollection.getNumGeometries(); i++) {
            if (!origCollection.getGeometryN(i).equals(newCollection.getGeometryN(i))) {
                assertTrue(false);
            }
        }
    }

    // Note: GeoJSONParser does not presently convert arbitrary JSON objects to Java objects
    // Thus the 'properties' attribute is simply carried over as JSON.
    // TODO: Generalize feature conversion to allow for more sophisticated object conversion.
    @Test
    public void testFeature() throws JSONException {
        GeometryFactory gf = new GeometryFactory();
        SimpleFeatureTypeBuilder builder = new SimpleFeatureTypeBuilder();
        builder.setName("none");

        builder.add("geometry", Geometry.class, DefaultGeographicCRS.WGS84);

        builder.add("properties", String.class);

        SimpleFeatureType featureType = builder.buildFeatureType();

        SimpleFeatureBuilder sfb = new SimpleFeatureBuilder(featureType);
        Object[] attributes = new Object[] { gf.createPoint(new Coordinate(1.0, 4.0)),
                "{\"prop\":1}" };

        SimpleFeature origFeature = sfb.buildFeature("myID", attributes);

        String jsonStr = "{\"type\": \"Feature\", "
                + "\"geometry\": {\"type\": \"Point\", \"coordinates\": [1.0, 4.0]},"
                + "\"properties\": { \"prop\": 1}," + "\"id\": \"myID\"}";

        SimpleFeature newFeature = (SimpleFeature) GeoJSONParser.parse(jsonStr);

        assertTrue(((Geometry) newFeature.getAttribute(0)).equals((Geometry) origFeature
                .getAttribute(0)));
        assertTrue(newFeature.getAttribute(1).toString().equals(
                origFeature.getAttribute(1).toString()));
        assertTrue(newFeature.getID().equals(origFeature.getID()));
    }

    // TODO: Finish test for FeatureCollection
    /*
     * public void testFeatureCollection() throws SchemaException, IllegalAttributeException,
     * GeoJSONException { GeometryFactory gf = new GeometryFactory(); FeatureTypeBuilder builder =
     * FeatureTypeBuilder.newInstance("none"); AttributeType attributeType =
     * AttributeTypeFactory.newAttributeType("geometry", Geometry.class);
     * builder.addType(attributeType); attributeType =
     * AttributeTypeFactory.newAttributeType("properties", String.class);
     * builder.addType(attributeType);
     * 
     * FeatureType featureType = builder.getFeatureType(); Object[] attributes1 = new Object[] {
     * gf.createPoint(new Coordinate(2.0, 2.0)), "{\"prop\":0}"}; Object[] attributes2 = new
     * Object[] { gf.createLineString(new Coordinate[] { new Coordinate(10, 10), new Coordinate(20,
     * 20) }), "\"prop\":0}"};
     * 
     * Feature feature1 = featureType.create(attributes1, "1"); Feature feature2 =
     * featureType.create(attributes2, "2");
     * 
     * DefaultFeatureCollection origCollection = new DefaultFeatureCollection("test", featureType);
     * origCollection.add(feature1); origCollection.add(feature2);
     * 
     * String jsonStr = "{\"type\": \"FeatureCollection\", \"features\":" +
     * "[{\"type\": \"Feature\", \"geometry\": {\"type\": \"Point\", \"coordinates\": [2.0, 2.0]},"
     * + "\"properties\": \"{\"prop\":0}}," +
     * "{\"type\": \"Feature\", \"geometry\": {\"type\": \"LineString\", \"coordinates\": [[10,10], [20,20]]}}]}"
     * ;
     * 
     * FeatureCollection newCollection = (FeatureCollection) GeoJSONParser.parse(jsonStr);
     * 
     * assertTrue(false); }
     */

    private JSONObject createJSONObject(Geometry g) {
        StringWriter sw = new StringWriter();
        new GeoJSONSerializer(sw).writeGeometry(g);

        return (JSONObject) JSONSerializer.toJSON(sw.toString());
    }
}
