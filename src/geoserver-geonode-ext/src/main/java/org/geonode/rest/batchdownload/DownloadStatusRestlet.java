package org.geonode.rest.batchdownload;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.json.JSONObject;

import org.geonode.process.control.ProcessController;
import org.geonode.process.control.ProcessStatus;
import org.geotools.util.logging.Logging;
import org.restlet.Restlet;
import org.restlet.data.MediaType;
import org.restlet.data.Method;
import org.restlet.data.Reference;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.Representation;
import org.restlet.resource.StringRepresentation;

/**
 * Returns the status code and progress percentage of a launched process.
 * <p>
 * Input: HTTP GET request to {@code <restlet end point>/<process id>}. For example:
 * {@code http://localhost:8080/geoserver/rest/process/batchdownload/status/1001}
 * </p>
 * <p>
 * Output: JSON object with the following structure:
 * 
 * <pre>
 * <code>
 * {
 *   process: {
 *     id: &lt;processId&gt;,
 *     status: "&lt;WAITING|RUNNING|FINISHED|FAILED&gt;",
 *     progress: &lt;percentage (0f - 100f)&gt;
 *   }
 * }
 * </code>
 * </pre>
 * 
 * </p>
 * 
 */
public class DownloadStatusRestlet extends Restlet {

    private static final Logger LOGGER = Logging.getLogger(DownloadStatusRestlet.class);

    private final ProcessController controller;

    public DownloadStatusRestlet(final ProcessController controller) {
        this.controller = controller;
    }

    public void handle(Request request, Response response) {
        if (!request.getMethod().equals(Method.GET)) {
            response.setStatus(Status.CLIENT_ERROR_METHOD_NOT_ALLOWED);
            return;
        }

        final Reference resourceRef = request.getResourceRef();
        final String lastSegment = resourceRef.getLastSegment();
        final Long processId;
        try {
            processId = Long.decode(lastSegment);
        } catch (NumberFormatException e) {
            response.setStatus(Status.CLIENT_ERROR_BAD_REQUEST, lastSegment
                    + " is not a valid process identifier");
            return;
        }

        ProcessStatus status;
        float progress;
        String errorMessage = null;
        try {
            status = controller.getStatus(processId);
            progress = controller.getProgress(processId);
            if (status == ProcessStatus.FAILED) {
                Throwable error = controller.getReasonForFailure(processId);
                if (error != null) {
                    errorMessage = error.getMessage();
                    if (LOGGER.isLoggable(Level.FINE)) {
                        ByteArrayOutputStream out = new ByteArrayOutputStream();
                        error.printStackTrace(new PrintStream(out));
                        String stackTrace = out.toString();
                        errorMessage += "\n" + stackTrace;
                    }
                }
            }
        } catch (IllegalArgumentException e) {
            response.setStatus(Status.CLIENT_ERROR_NOT_FOUND, e.getMessage());
            return;
        }

        final JSONObject responseData = new JSONObject();
        final JSONObject processData = new JSONObject();
        processData.put("id", processId);
        processData.put("status", status.toString());
        processData.put("progress", progress);
        processData.put("reasonForFailure", errorMessage);
        responseData.put("process", processData);

        final String jsonStr = responseData.toString(0);
        final Representation representation = new StringRepresentation(jsonStr,
                MediaType.APPLICATION_JSON);

        response.setEntity(representation);
    }
}
