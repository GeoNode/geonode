package org.geonode.rest;

import org.geoserver.test.GeoServerTestSupport;
import com.mockrunner.mock.web.MockHttpServletResponse;

public class ProcessRestTest extends GeoServerTestSupport {
    public void testServiceExists() throws Exception {
        MockHttpServletResponse r = getAsServletResponse("/rest/process/hazard");
        assertEquals(200, r.getStatusCode());
    }
}
