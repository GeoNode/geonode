package org.geonode.rest.batchdownload;

import static org.restlet.data.Status.CLIENT_ERROR_BAD_REQUEST;
import static org.restlet.data.Status.CLIENT_ERROR_EXPECTATION_FAILED;
import static org.restlet.data.Status.SUCCESS_OK;

import javax.xml.namespace.QName;

import junit.framework.Test;

import org.geoserver.data.test.MockData;
import org.geoserver.test.GeoServerTestSupport;
import org.restlet.data.Status;

import com.mockrunner.mock.web.MockHttpServletResponse;

public class DownloadLauncherRestletTest extends GeoServerTestSupport {

    private static final String RESTLET_PATH = "/rest/process/batchDownload/launch";

    private static final QName VECTOR_LAYER = MockData.DIVIDED_ROUTES;

    private static final QName RASTER_LAYER = MockData.TASMANIA_DEM;

    /**
     * This is a READ ONLY TEST so we can use one time setup
     */
    public static Test suite() {
        return new OneTimeTestSetup(new DownloadLauncherRestletTest());
    }

    @Override
    protected void populateDataDirectory(MockData dataDirectory) throws Exception {
        super.populateDataDirectory(dataDirectory);
        dataDirectory.addWellKnownCoverageTypes();
    }

    public void testHTTPMethod() throws Exception {
        MockHttpServletResponse r = getAsServletResponse(RESTLET_PATH);
        assertEquals(Status.CLIENT_ERROR_METHOD_NOT_ALLOWED.getCode(), r.getStatusCode());
    }

    public void testPreconditions() throws Exception {
        String jsonRequest;

        jsonRequest = "not a json object";
        testRequest(jsonRequest, CLIENT_ERROR_BAD_REQUEST);

        jsonRequest = "{map:{}}";
        testRequest(jsonRequest, CLIENT_ERROR_EXPECTATION_FAILED);

        jsonRequest = "{map:{name:''}}";
        testRequest(jsonRequest, CLIENT_ERROR_EXPECTATION_FAILED);

        jsonRequest = "{map:{name:'fake Map'}}";
        testRequest(jsonRequest, CLIENT_ERROR_EXPECTATION_FAILED);

        jsonRequest = "{map:{name:'fake Map', author:'myself'}, layers:[{name:'fakeLayer'}]}";
        testRequest(jsonRequest, CLIENT_ERROR_EXPECTATION_FAILED);

        jsonRequest = "{map:{name:'fake Map', author:'myself'}, layers:[{name:'fakeLayer', service:'NotAnOWS'}]}";
        testRequest(jsonRequest, CLIENT_ERROR_EXPECTATION_FAILED);

        jsonRequest = "{map:{name:'fake Map', author:'myself'}, layers:[{name:'fakeLayer', service:'WFS', metadataURL:'not an url'}]}";
        testRequest(jsonRequest, CLIENT_ERROR_EXPECTATION_FAILED);
    }

    public void testVectorLayer() throws Exception {
        String jsonRequest;
        String layerName = VECTOR_LAYER.getPrefix() + ":" + VECTOR_LAYER.getLocalPart();
        jsonRequest = "{map:{name:'fake Map', author:'myself'}, "
                + " layers:[{name:'"
                + layerName
                + "', service:'WFS', metadataURL:'', serviceURL='http://localhost/it/doesnt/matter/so/far'}]}";

        testRequest(jsonRequest, SUCCESS_OK);

    }

    public MockHttpServletResponse testRequest(final String jsonRequest,
            final Status expectedResponseCode) throws Exception {
        MockHttpServletResponse response;
        response = postAsServletResponse(RESTLET_PATH, jsonRequest);
        assertEquals(expectedResponseCode, Status.valueOf(response.getStatusCode()));
        return response;
    }
}
