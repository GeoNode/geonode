package org.geonode.geojson;

import static org.junit.Assert.assertEquals;

import java.io.StringWriter;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.io.WKTReader;

/**
 * Unit test suite for the {@link GeoJSONSerializer} that exercises writing GeoJSON objects as
 * defined in <a href="http://geojson.org/geojson-spec.html#geojson-objects">the GeoJSON spec</a>.
 * 
 */
public class GeoJSONSerializerTest {

    private static final GeometryFactory gf = new GeometryFactory();

    private static final WKTReader wkt = new WKTReader();

    private GeoJSONSerializer serializer;

    private StringWriter writer;

    @Before
    public void setUp() throws Exception {
        writer = new StringWriter();
        serializer = new GeoJSONSerializer(writer);
    }

    @After
    public void tearDown() throws Exception {
    }

    @Test
    public void testPoint() throws Exception {
        Geometry point = wkt.read("POINT(10 20)");
        serializer.writeGeometry(point);
        writer.flush();
        String expected = "{\"type\":\"Point\",\"coordinates\":[10,20,0]}";
        String jsonStr = writer.toString();
        assertEquals(expected, jsonStr);
    }

    @Test
    public void testLineString() throws Exception {
        Geometry lineString = wkt.read("LINESTRING(10 20, 20 30, 30 40)");
        serializer.writeGeometry(lineString);
        writer.flush();
        String expected = "{\"type\":\"LineString\",\"coordinates\":[[10,20,0],[20,30,0],[30,40,0]]}";
        String jsonStr = writer.toString();
        assertEquals(expected, jsonStr);
    }

    @Test
    public void testLinePolygonSimple() throws Exception {
        Geometry polygon = wkt.read("POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))");
        serializer.writeGeometry(polygon);
        writer.flush();
        String expected = "{\"type\":\"Polygon\",\"coordinates\":[[[0,0,0],[0,10,0],[10,10,0],[10,0,0],[0,0,0]]]}";
        String jsonStr = writer.toString();
        assertEquals(expected, jsonStr);
    }

    @Test
    public void testLinePolygonWithHoles() throws Exception {
        Geometry polygonWithHoles = wkt
                .read("POLYGON((0 0, 0 10, 10 10, 10 0, 0 0),(2 2, 2 3, 3 3, 3 2, 2 2),(6 6, 6 7, 7 7, 7 6, 6 6) )");
        serializer.writeGeometry(polygonWithHoles);
        writer.flush();
        String expected = "{\"type\":\"Polygon\",\"coordinates\":[[[0,0,0],[0,10,0],[10,10,0],[10,0,0],[0,0,0]],[[2,2,0],[2,3,0],[3,3,0],[3,2,0],[2,2,0]],[[6,6,0],[6,7,0],[7,7,0],[7,6,0],[6,6,0]]]}";
        String jsonStr = writer.toString();
        assertEquals(expected, jsonStr);
    }
}
