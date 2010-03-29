package org.geonode.geojson;

import java.io.StringWriter;

import junit.framework.TestCase;
import net.sf.json.JSONObject;
import net.sf.json.test.JSONAssert;

import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.io.WKTReader;

/**
 * Unit test suite for the {@link GeoJSONSerializer} that exercises writing GeoJSON objects as
 * defined in <a href="http://geojson.org/geojson-spec.html#geojson-objects">the GeoJSON spec</a>.
 * 
 */
public class GeoJSONSerializerTest extends TestCase {

    private static final WKTReader wkt = new WKTReader();

    private GeoJSONSerializer serializer;

    private StringWriter writer;

    @Override
    public void setUp() throws Exception {
        writer = new StringWriter();
        serializer = new GeoJSONSerializer(writer);
    }

    @Override
    public void tearDown() throws Exception {
    }

    public void testPoint() throws Exception {
        Geometry point = wkt.read("POINT(10 20)");
        serializer.writeGeometry(point);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"Point\",\"coordinates\":[10,20,0]}");
        JSONObject actual = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, actual);
    }

    public void testLineString() throws Exception {
        Geometry lineString = wkt.read("LINESTRING(10 20, 20 30, 30 40)");
        serializer.writeGeometry(lineString);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"LineString\",\"coordinates\":[[10,20,0],[20,30,0],[30,40,0]]}");
        JSONObject actual = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, actual);
    }

    public void testLinePolygonSimple() throws Exception {
        Geometry polygon = wkt.read("POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))");
        serializer.writeGeometry(polygon);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"Polygon\",\"coordinates\":[[[0,0,0],[0,10,0],[10,10,0],[10,0,0],[0,0,0]]]}");
        JSONObject actual = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, actual);
    }

    public void testLinePolygonWithHoles() throws Exception {
        Geometry polygonWithHoles = wkt
                .read("POLYGON((0 0, 0 10, 10 10, 10 0, 0 0),(2 2, 2 3, 3 3, 3 2, 2 2),(6 6, 6 7, 7 7, 7 6, 6 6) )");
        serializer.writeGeometry(polygonWithHoles);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"Polygon\",\"coordinates\":[[[0,0,0],[0,10,0],[10,10,0],[10,0,0],[0,0,0]],[[2,2,0],[2,3,0],[3,3,0],[3,2,0],[2,2,0]],[[6,6,0],[6,7,0],[7,7,0],[7,6,0],[6,6,0]]]}");
        JSONObject jsonStr = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, jsonStr);
    }

    public void testMultiPoint() throws Exception {
        Geometry point = wkt.read("MULTIPOINT(10 20, 30 40)");
        serializer.writeGeometry(point);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"MultiPoint\",\"coordinates\":[[10,20,0],[30,40,0]]}");
        JSONObject actual = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, actual);
    }

    public void testMultiLineString() throws Exception {
        Geometry lineString = wkt
                .read("MULTILINESTRING((10 20, 20 30, 30 40), (0 0, 1 1, 2 2, 3 3))");
        serializer.writeGeometry(lineString);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"MultiLineString\",\"coordinates\":[ [[10,20,0],[20,30,0],[30,40,0]], [[0,0,0],[1,1,0],[2,2,0],[3,3,0]] ]}");
        JSONObject actual = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, actual);
    }

    public void testMultiPolygon() throws Exception {
        Geometry multiPolygon = wkt
                .read("MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)), ((0 0, 0 10, 10 10, 10 0, 0 0),(2 2, 2 3, 3 3, 3 2, 2 2),(6 6, 6 7, 7 7, 7 6, 6 6)))");
        serializer.writeGeometry(multiPolygon);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"MultiPolygon\",\"coordinates\":[[[[0,0,0],[0,1,0],[1,1,0],[1,0,0],[0,0,0]]],"
                        + "[[[0,0,0],[0,10,0],[10,10,0],[10,0,0],[0,0,0]],[[2,2,0],[2,3,0],[3,3,0],[3,2,0],[2,2,0]],[[6,6,0],[6,7,0],[7,7,0],[7,6,0],[6,6,0]]]]}");
        JSONObject jsonStr = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, jsonStr);
    }

    public void testGeometryCollection() throws Exception {
        Geometry geometryCollection = wkt.read("GEOMETRYCOLLECTION("
                + //
                "  POINT(10 20)"
                + //
                ", LINESTRING(10 20, 20 30, 30 40)"
                + //
                ", POLYGON((0 0, 0 10, 10 10, 10 0, 0 0),(2 2, 2 3, 3 3, 3 2, 2 2),(6 6, 6 7, 7 7, 7 6, 6 6) )"
                + //
                ")");

        serializer.writeGeometry(geometryCollection);
        writer.flush();

        JSONObject expected = JSONObject
                .fromObject("{\"type\":\"GeometryCollection\",\"geometries\":["
                        + "{\"type\":\"Point\",\"coordinates\":[10,20,0]},"
                        + "{\"type\":\"LineString\",\"coordinates\":[[10,20,0],[20,30,0],[30,40,0]]},"
                        + "{\"type\":\"Polygon\",\"coordinates\":[[[0,0,0],[0,10,0],[10,10,0],[10,0,0],[0,0,0]],[[2,2,0],[2,3,0],[3,3,0],[3,2,0],[2,2,0]],[[6,6,0],[6,7,0],[7,7,0],[7,6,0],[6,6,0]]]}"
                        + "]}");
        JSONObject jsonStr = JSONObject.fromObject(writer.toString());
        JSONAssert.assertEquals(expected, jsonStr);
    }
}
