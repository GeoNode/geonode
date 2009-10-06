package org.geonode.geojson;

import static net.sf.json.test.JSONAssert.*;

import java.io.StringWriter;

import net.sf.json.test.JSONAssert;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;

/**
 * Unit test suite for the {@link GeoJSONSerializer} that exercises writing GeoJSON objects as
 * defined in <a href="http://geojson.org/geojson-spec.html#geojson-objects">the GeoJSON spec</a>.
 * 
 */
public class GeoJSONSerializerTest {

    private static final GeometryFactory gf = new GeometryFactory();

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
    public void testPoint() {
        serializer.point(gf.createPoint(new Coordinate(10, 20)));
        writer.flush();
        System.out.println(writer.toString());
    }
}
