package org.geonode.geojson;

import java.io.StringWriter;

import junit.framework.TestCase;
import net.sf.json.JSONException;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

import org.geotools.feature.simple.SimpleFeatureBuilder;
import org.geotools.feature.simple.SimpleFeatureTypeBuilder;
import org.geotools.referencing.CRS;
import org.geotools.referencing.crs.DefaultGeographicCRS;
import org.opengis.feature.simple.SimpleFeature;
import org.opengis.feature.simple.SimpleFeatureType;
import org.opengis.referencing.NoSuchAuthorityCodeException;
import org.opengis.referencing.crs.CoordinateReferenceSystem;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryCollection;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.LineString;
import com.vividsolutions.jts.geom.MultiLineString;
import com.vividsolutions.jts.geom.MultiPoint;
import com.vividsolutions.jts.geom.MultiPolygon;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.Polygon;
import com.vividsolutions.jts.io.WKTReader;

public class GeoJSONParserTest extends TestCase {

    private static final WKTReader wkt = new WKTReader();

    private GeoJSONParser parser;

    /**
     * TODO: change this to a GeoTools config when the GeoJSONConfig interface is abstracted out
     */
    private GeoJSONConfig config = new GeoJSONConfig();

    @Override
    public void setUp() throws Exception {
        parser = new GeoJSONParser(config);
    }

    @Override
    public void tearDown() throws Exception {
    }

    public void testPoint() throws Exception {
        Point origPoint = (Point) wkt.read("POINT(120 0)");

        JSONObject jsonObj = createJSONObject(origPoint);

        Point newPoint = (Point) GeoJSONParser.parse(jsonObj);

        assertTrue(newPoint.equals(origPoint));
    }

    public void testLineString() throws Exception {
        LineString origLine = (LineString) wkt
                .read("LINESTRING(20.2 10.1, 12.4 1, 12.4 5.5, 14 42)");

        JSONObject jsonObj = createJSONObject(origLine);

        LineString newLine = (LineString) GeoJSONParser.parse(jsonObj);

        assertTrue(newLine.equals(origLine));
    }

    public void testPolygon() throws Exception {
        Polygon origPoly = (Polygon) wkt.read("POLYGON((0 1, 1.2 0.12, 1.4 1, 0 1))");

        JSONObject jsonObj = createJSONObject(origPoly);

        Polygon newPoly = (Polygon) GeoJSONParser.parse(jsonObj);

        assertTrue(newPoly.equals(origPoly));
    }

    public void testMultiPoint() throws Exception {
        MultiPoint origPoints = (MultiPoint) wkt.read("MULTIPOINT(142 142, 202 128, 84 8)");

        JSONObject jsonObj = createJSONObject(origPoints);

        MultiPoint newPoints = (MultiPoint) GeoJSONParser.parse(jsonObj);

        assertTrue(newPoints.equals(origPoints));
    }

    public void testMultiLineString() throws Exception {
        MultiLineString origMLS = (MultiLineString) wkt
                .read("MULTILINESTRING((0 0, 1 2), (3 2, 4 2))");

        JSONObject jsonObj = createJSONObject(origMLS);

        MultiLineString newMLS = (MultiLineString) GeoJSONParser.parse(jsonObj);

        assertTrue(newMLS.equals(origMLS));
    }

    public void testMultiPolygon() throws Exception {
        MultiPolygon origMultiPoly = (MultiPolygon) wkt
                .read("MULTIPOLYGON(((0 0, 1 1, 1 2, 0 2, 0 0)), ((10 10, 10 14, 5 12, 10 10)))");

        JSONObject jsonObj = createJSONObject(origMultiPoly);

        MultiPolygon newMultiPoly = (MultiPolygon) GeoJSONParser.parse(jsonObj);

        assertTrue(newMultiPoly.equals(origMultiPoly));
    }

    public void testGeometryCollection() throws Exception {
        GeometryCollection origCollection = (GeometryCollection) wkt
                .read("GEOMETRYCOLLECTION(POINT(1 1.4), LINESTRING(32 64, 192 160), POINT(2 2))");

        JSONObject jsonObj = createJSONObject(origCollection);

        GeometryCollection newCollection = (GeometryCollection) GeoJSONParser.parse(jsonObj);

        if (origCollection.getNumGeometries() != newCollection.getNumGeometries()) {
            assertTrue(false);
        }

        for (int i = 0; i < origCollection.getNumGeometries(); i++) {
            assertTrue(origCollection.getGeometryN(i).equals(newCollection.getGeometryN(i)));
        }
    }

    public void testParseNamedCrsUnknownAuthority() throws Exception {
        // GeoJSON CRS's can't live as standalone objects, they're identified as
        // the "crs" property
        // of a container object
        String jsonStr = "{\"type\":\"Point\", \"coordinates\": [100.0, 0.0],"
                + "\"crs\":{\"type\": \"name\",\"properties\": {\"name\": \"urn:ogc:def:crs:OGC:1.3:CRS84\"}}}";
        try {
            GeoJSONParser.parse(jsonStr);
            fail("expected NoSuchAuthorityCodeException");
        } catch (JSONException e) {
            assertTrue(e.getCause() instanceof NoSuchAuthorityCodeException);
        }
    }

    public void testParseNamedCrs() throws Exception {
        // GeoJSON CRS's can't live as standalone objects, they're identified as
        // the "crs" property
        // of a container object
        String jsonStr = "{\"type\":\"Point\", \"coordinates\": [100.0, 0.0],"
                + "\"crs\":{\"type\": \"name\",\"properties\": {\"name\": \"EPSG:4326\"}}}";

        Object parsed = GeoJSONParser.parse(jsonStr);
        assertNotNull(parsed);

        CoordinateReferenceSystem expected = CRS.decode("EPSG:4326", true);

        assertTrue(parsed instanceof Point);
        assertTrue(((Point) parsed).getUserData() instanceof CoordinateReferenceSystem);
        assertTrue(CRS.equalsIgnoreMetadata(expected, ((Point) parsed).getUserData()));
    }

    public void testParseLinkedCrsIsUnsupported() throws Exception {
        // GeoJSON CRS's can't live as standalone objects, they're identified as
        // the "crs" property
        // of a container object.
        // Linked CRSs are not supported:
        String jsonStr = "{\"type\":\"Point\", \"coordinates\": [100.0, 0.0],"
                + "\"crs\":{\"type\": \"link\",\"properties\": {\"href\": \"http://example.com/crs/42\", \"type\": \"proj4\"}}}";

        try {
            GeoJSONParser.parse(jsonStr);
            fail("Expected UnsupportedOperationException for linked CRS's");
        } catch (UnsupportedOperationException e) {
            assertTrue(true);
        }
    }

    // Note: GeoJSONParser does not presently convert arbitrary JSON objects to
    // Java objects
    // Thus the 'properties' attribute is simply carried over as JSON.
    // TODO: Generalize feature conversion to allow for more sophisticated
    // object conversion.
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

        assertTrue(((Geometry) newFeature.getAttribute("geometry")).equals((Geometry) origFeature
                .getAttribute("geometry")));
        assertTrue(newFeature.getAttribute("properties").toString()
                .equals(origFeature.getAttribute("properties").toString()));
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
