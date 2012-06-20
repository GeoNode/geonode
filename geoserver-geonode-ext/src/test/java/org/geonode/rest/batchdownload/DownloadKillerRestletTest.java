package org.geonode.rest.batchdownload;

import static org.geonode.rest.batchdownload.BatchDownloadTestData.RESTLET_BASE_PATH;

import java.util.Collections;
import java.util.Map;

import junit.framework.Test;

import org.geonode.GeoNodeTestSupport;
import org.geonode.process.control.AsyncProcess;
import org.geonode.process.control.ProcessController;
import org.geoserver.data.test.MockData;
import org.geoserver.platform.GeoServerExtensions;
import org.geotools.process.ProcessException;
import org.opengis.util.ProgressListener;
import org.restlet.data.Status;

import com.mockrunner.mock.web.MockHttpServletResponse;

public class DownloadKillerRestletTest extends GeoNodeTestSupport {

    private static final String RESTLET_PATH = RESTLET_BASE_PATH + "/kill";

    /**
     * This is a READ ONLY TEST so we can use one time setup
     */
    public static Test suite() {
        return new OneTimeTestSetup(new DownloadKillerRestletTest());
    }

    @Override
    protected void populateDataDirectory(MockData dataDirectory) throws Exception {
        super.populateDataDirectory(dataDirectory);
        dataDirectory.addWcs11Coverages();
    }

    public void testHTTPMethod() throws Exception {
        MockHttpServletResponse r = postAsServletResponse(RESTLET_PATH, "");
        assertEquals(Status.CLIENT_ERROR_METHOD_NOT_ALLOWED, Status.valueOf(r.getStatusCode()));
    }

    public void testInvalidProcessId() throws Exception {
        String request = RESTLET_PATH + "/notAProcessId";
        MockHttpServletResponse r = getAsServletResponse(request);
        assertEquals(Status.CLIENT_ERROR_BAD_REQUEST, Status.valueOf(r.getStatusCode()));
    }

    public void testNonExistentProcess() throws Exception {
        String request = RESTLET_PATH + "/10000";
        MockHttpServletResponse r = getAsServletResponse(request);
        assertEquals(Status.CLIENT_ERROR_NOT_FOUND, Status.valueOf(r.getStatusCode()));
    }

    public void testKillRunningProcess() throws Exception {

        ProcessController controller = (ProcessController) GeoServerExtensions
                .bean("processController");

        final Long processId = issueProcess(10);

        assertFalse(controller.isDone(processId));

        final String request = RESTLET_PATH + "/" + processId.longValue();

        final MockHttpServletResponse response = getAsServletResponse(request);
        assertEquals(Status.SUCCESS_OK, Status.valueOf(response.getStatusCode()));
    }

    public void testKillFinishedProcess() throws Exception {

        ProcessController controller = (ProcessController) GeoServerExtensions
                .bean("processController");

        final Long processId = issueProcess(1);
        Thread.sleep(2000);

        assertTrue(controller.isDone(processId));

        final String request = RESTLET_PATH + "/" + processId.longValue();

        final MockHttpServletResponse response = getAsServletResponse(request);
        assertEquals(Status.SUCCESS_NO_CONTENT, Status.valueOf(response.getStatusCode()));
    }

    /**
     * Issues a fake process that finishes normally after {@code timeOutSeconds} seconds if not
     * killed
     * 
     * @param i
     * 
     * @return
     * @throws Exception
     */
    private Long issueProcess(final int timeOutSeconds) throws Exception {

        ProcessController controller = (ProcessController) GeoServerExtensions
                .bean("processController");

        AsyncProcess process = new AsyncProcess() {
            @Override
            protected Map<String, Object> executeInternal(final Map<String, Object> input,
                    final ProgressListener monitor) throws ProcessException {

                final long launchTime = System.currentTimeMillis();
                while (System.currentTimeMillis() - launchTime < timeOutSeconds * 1000L) {
                    try {
                        Thread.sleep(100);
                    } catch (InterruptedException e) {
                        throw new ProcessException(e);
                    }
                    if (monitor.isCanceled()) {
                        return null;
                    }
                }
                return Collections.emptyMap();
            }
        };
        Map<String, Object> processInputs = Collections.emptyMap();
        final Long processId = controller.submitAsync(process, processInputs);

        return processId;
    }
}
