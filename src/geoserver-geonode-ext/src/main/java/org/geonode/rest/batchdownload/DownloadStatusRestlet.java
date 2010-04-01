package org.geonode.rest.batchdownload;

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
 * 
 *
 */
public class DownloadStatusRestlet extends Restlet {

    private static Logger LOGGER = Logging.getLogger(DownloadStatusRestlet.class);

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
        try {
            status = controller.getStatus(processId);
        } catch (IllegalArgumentException e) {
            response.setStatus(Status.CLIENT_ERROR_NOT_FOUND, e.getMessage());
            return;
        }

        final JSONObject responseData = new JSONObject();
        final JSONObject processData = new JSONObject();
        processData.put("id", 12);
        processData.put("status", status.toString());
        processData.put("processing", "topp:states");
        processData.put("totalLayers", 12);
        responseData.put("process", processData);

        final String jsonStr = responseData.toString(0);
        final Representation representation = new StringRepresentation(jsonStr,
                MediaType.APPLICATION_JSON);

        response.setEntity(representation);
    }
}
