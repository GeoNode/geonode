package org.geonode.rest.batchdownload;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Map;

import org.apache.commons.io.IOUtils;
import org.geonode.process.batchdownload.BatchDownloadFactory;
import org.geonode.process.control.ProcessController;
import org.geonode.process.storage.Resource;
import org.restlet.Restlet;
import org.restlet.data.MediaType;
import org.restlet.data.Method;
import org.restlet.data.Reference;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.OutputRepresentation;
import org.restlet.resource.Representation;

/**
 * Serves out the resulting zip file for a finished batch download process.
 * <p>
 * Input: HTTP GET request to {@code <restlet end point>/<process id>}. For example:
 * {@code http://localhost:8080/geoserver/rest/process/batchdownload/download/1001}
 * </p>
 * <p>
 * Output: ZIP file
 * </p>
 * 
 */
public class DownloadReadyRestlet extends Restlet {

    private final ProcessController controller;

    public DownloadReadyRestlet(final ProcessController controller) {
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

        Map<String, Object> result;
        try {
            result = controller.getResult(processId);
        } catch (IllegalArgumentException e) {
            response.setStatus(Status.CLIENT_ERROR_NOT_FOUND, e.getMessage());
            return;
        }

        final Resource zipRes = (Resource) result.get(BatchDownloadFactory.RESULT_ZIP.key);

        final InputStream zip;
        try {
            zip = zipRes.getInputStream();
        } catch (IOException e) {
            response.setStatus(Status.SERVER_ERROR_INTERNAL, e.getMessage());
            return;
        }

        final Representation representation = new OutputRepresentation(MediaType.APPLICATION_ZIP) {
            public void write(OutputStream out) throws IOException {
                try {
                    IOUtils.copy(zip, out);
                } finally {
                    zip.close();
                }
            }
        };

        try {
            File file = zipRes.getFile();
            long fileSize = file.length();
            representation.setSize(fileSize);
        } catch (Exception e) {
            // no worries, may the resource be not referencing a file in the filesystem but some
            // other kind of resource
        }
        response.setEntity(representation);
    }
}
