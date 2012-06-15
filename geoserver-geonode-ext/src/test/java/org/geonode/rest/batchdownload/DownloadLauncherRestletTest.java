package org.geonode.rest.batchdownload;

import static org.geonode.rest.batchdownload.BatchDownloadTestData.RASTER_LAYER;
import static org.geonode.rest.batchdownload.BatchDownloadTestData.RASTER_LAYER_REQUEST_NO_METADATA;
import static org.geonode.rest.batchdownload.BatchDownloadTestData.RESTLET_BASE_PATH;
import static org.geonode.rest.batchdownload.BatchDownloadTestData.VECTOR_AND_RASTER_REQUEST_NO_METADATA;
import static org.geonode.rest.batchdownload.BatchDownloadTestData.VECTOR_AND_RASTER_REQUEST_WITH_METADATA;
import static org.geonode.rest.batchdownload.BatchDownloadTestData.VECTOR_LAYER;
import static org.geonode.rest.batchdownload.BatchDownloadTestData.VECTOR_LAYER_REQUEST_NO_METADATA;
import static org.restlet.data.Status.CLIENT_ERROR_BAD_REQUEST;
import static org.restlet.data.Status.CLIENT_ERROR_EXPECTATION_FAILED;
import static org.restlet.data.Status.SUCCESS_OK;

import java.io.InputStream;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import junit.framework.Test;
import net.sf.json.JSONObject;

import org.geonode.GeoNodeTestSupport;
import org.geonode.process.batchdownload.BatchDownloadFactory;
import org.geonode.process.control.ProcessController;
import org.geonode.process.control.ProcessStatus;
import org.geonode.process.storage.Resource;
import org.geoserver.data.test.MockData;
import org.geoserver.platform.GeoServerExtensions;
import org.restlet.data.Status;

import com.mockrunner.mock.web.MockHttpServletResponse;

public class DownloadLauncherRestletTest extends GeoNodeTestSupport {

    private static final String RESTLET_PATH = RESTLET_BASE_PATH + "/launch";

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
        jsonRequest = VECTOR_LAYER_REQUEST_NO_METADATA;

        MockHttpServletResponse response = testRequest(jsonRequest, SUCCESS_OK);
        String outputStreamContent = response.getOutputStreamContent();
        assertNotNull(outputStreamContent);
        JSONObject jsonResponse = JSONObject.fromObject(outputStreamContent);
        assertTrue(jsonResponse.containsKey("id"));
        assertNotNull(jsonResponse.getString("id"));

        final Long processId = Long.valueOf(jsonResponse.getString("id"));

        ProcessController controller = (ProcessController) GeoServerExtensions
                .bean("processController");

        // wait for the process to finish....
        while (!controller.isDone(processId)) {
            Thread.sleep(100);
        }
        ProcessStatus status = controller.getStatus(processId);
        assertEquals(ProcessStatus.FINISHED, status);
    }

    public void testRasterLayer() throws Exception {
        String jsonRequest = RASTER_LAYER_REQUEST_NO_METADATA;

        MockHttpServletResponse response = testRequest(jsonRequest, SUCCESS_OK);
        String outputStreamContent = response.getOutputStreamContent();
        assertNotNull(outputStreamContent);
        JSONObject jsonResponse = JSONObject.fromObject(outputStreamContent);
        assertTrue(jsonResponse.containsKey("id"));
        assertNotNull(jsonResponse.getString("id"));

        final Long processId = Long.valueOf(jsonResponse.getString("id"));

        ProcessController controller = (ProcessController) GeoServerExtensions
                .bean("processController");

        // wait for the process to finish....
        while (!controller.isDone(processId)) {
            Thread.sleep(100);
        }
        ProcessStatus status = controller.getStatus(processId);
        assertEquals(ProcessStatus.FINISHED, status);
    }

    // public void testArcSDERasterLayer() throws Exception {
    // ProcessController controller = (ProcessController) GeoServerExtensions
    // .bean("processController");
    //
    // AbstractGridCoverage2DReader reader = new ArcSDERasterFormatFactory().createFormat()
    // .getReader("sde://sde:geo123@arcy.opengeo.org:5151/#SDE.BH_30MHS_RD");
    // LayerReference layerReference = new LayerReference("SDE.BH_30MHS_RD", reader);
    // MapMetadata map = new MapMetadata("title", "abstract", "groldan");
    // Map<String, Object> input = new HashMap<String, Object>();
    // input.put(BatchDownloadFactory.MAP_METADATA.key, map);
    // input.put(BatchDownloadFactory.LAYERS.key, Collections.singletonList(layerReference));
    //
    // AsyncProcess process = new BatchDownloadFactory().create();
    //
    // Long processId = controller.submitAsync(process, input);
    //
    // // wait for the process to finish....
    // while (!controller.isDone(processId)) {
    // Thread.sleep(100);
    // }
    // ProcessStatus status = controller.getStatus(processId);
    // assertEquals(ProcessStatus.FINISHED, status);
    // }

    public void testVectorAndRasterLayer() throws Exception {
        String jsonRequest = VECTOR_AND_RASTER_REQUEST_NO_METADATA;

        Set<String> expectedFiles = new HashSet<String>();
        expectedFiles.add("README.txt");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".shp");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".cst");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".prj");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".dbf");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".shx");
        // TODO: change this expectation once we normalize the raster file name
        expectedFiles.add(RASTER_LAYER.getPrefix() + ":" + RASTER_LAYER.getLocalPart() + ".tiff");

        testSuccessfullRequestContents(jsonRequest, expectedFiles);

    }

    public void testVectorAndRasterLayerWithMetadata() throws Exception {
        String jsonRequest = VECTOR_AND_RASTER_REQUEST_WITH_METADATA;

        Set<String> expectedFiles = new HashSet<String>();
        expectedFiles.add("README.txt");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".shp");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".cst");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".prj");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".dbf");
        expectedFiles.add(VECTOR_LAYER.getLocalPart() + ".shx");
        // TODO: change this expectation once we normalize the raster file name
        expectedFiles.add(RASTER_LAYER.getPrefix() + ":" + RASTER_LAYER.getLocalPart() + ".tiff");

        String vlayerName = VECTOR_LAYER.getPrefix() + "_" + VECTOR_LAYER.getLocalPart() + ".xml";
        String rlayerName = RASTER_LAYER.getPrefix() + "_" + RASTER_LAYER.getLocalPart() + ".xml";
        expectedFiles.add(vlayerName);
        expectedFiles.add(rlayerName);

        testSuccessfullRequestContents(jsonRequest, expectedFiles);
    }

    private void testSuccessfullRequestContents(final String jsonRequest,
            final Set<String> expectedFiles) throws Exception {

        MockHttpServletResponse response = testRequest(jsonRequest, SUCCESS_OK);
        String outputStreamContent = response.getOutputStreamContent();
        assertNotNull(outputStreamContent);
        JSONObject jsonResponse = JSONObject.fromObject(outputStreamContent);
        assertTrue(jsonResponse.containsKey("id"));
        assertNotNull(jsonResponse.getString("id"));

        final Long processId = Long.valueOf(jsonResponse.getString("id"));

        ProcessController controller = (ProcessController) GeoServerExtensions
                .bean("processController");

        // wait for the process to finish....
        while (!controller.isDone(processId)) {
            Thread.sleep(100);
        }
        ProcessStatus status = controller.getStatus(processId);
        assertEquals(ProcessStatus.FINISHED, status);

        Map<String, Object> result = controller.getResult(processId);
        Resource zipRes = (Resource) result.get(BatchDownloadFactory.RESULT_ZIP.key);
        assertNotNull(zipRes);

        Set<String> archivedFiles = new HashSet<String>();

        InputStream inputStream = zipRes.getInputStream();
        ZipInputStream zipIn = new ZipInputStream(inputStream);
        ZipEntry nextEntry;
        while ((nextEntry = zipIn.getNextEntry()) != null) {
            archivedFiles.add(nextEntry.getName());
        }

        assertEquals(expectedFiles, archivedFiles);
    }

    public MockHttpServletResponse testRequest(final String jsonRequest,
            final Status expectedResponseCode) throws Exception {
        MockHttpServletResponse response;
        response = postAsServletResponse(RESTLET_PATH, jsonRequest);
        assertEquals(expectedResponseCode, Status.valueOf(response.getStatusCode()));
        return response;
    }
}
