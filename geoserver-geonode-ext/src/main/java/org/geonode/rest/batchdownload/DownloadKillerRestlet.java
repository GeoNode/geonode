package org.geonode.rest.batchdownload;

import org.geonode.process.control.ProcessController;
import org.restlet.Restlet;
import org.restlet.data.Method;
import org.restlet.data.Reference;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;

/**
 * Kills an ongoing batch download process.
 * <p>
 * Input: HTTP GET request to {@code <restlet end point>/<process id>}. For example:
 * {@code http://localhost:8080/geoserver/rest/process/batchdownload/kill/1001}.
 * </p>
 * <p>
 * Output: no content. Response status will be {@code 200 (OK)} if the process were running and has
 * been killed, or {@code 204 (SUCCESS NO CONTENT)} if the process has already finished at the time
 * the kill signal was sent. {@code 404 NOT FOUND} will be returned if the process didn't exist.
 * </p>
 */
public class DownloadKillerRestlet extends Restlet {

    private final ProcessController controller;

    public DownloadKillerRestlet(final ProcessController controller) {
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

        boolean killed;
        try {
            killed = controller.kill(processId);
        } catch (IllegalArgumentException e) {
            response.setStatus(Status.CLIENT_ERROR_NOT_FOUND, e.getMessage());
            return;
        }

        if (killed) {
            response.setStatus(Status.SUCCESS_OK);
        } else {
            response.setStatus(Status.SUCCESS_NO_CONTENT);
        }
    }
}
