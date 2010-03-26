package org.geonode.rest.batchdownload;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.json.JSONObject;

import org.apache.commons.io.IOUtils;
import org.geoserver.catalog.Catalog;
import org.geotools.util.logging.Logging;
import org.restlet.Restlet;
import org.restlet.data.MediaType;
import org.restlet.data.Method;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.OutputRepresentation;
import org.restlet.resource.Representation;

public class DownloadReadyRestlet extends Restlet {
    private Catalog catalog;

    private static Logger LOGGER = Logging.getLogger(DownloadReadyRestlet.class);

    public DownloadReadyRestlet(final Catalog catalog) {
        this.catalog = catalog;
    }

    public void handle(Request request, Response response) {
        if (!request.getMethod().equals(Method.GET)) {
            response.setStatus(Status.CLIENT_ERROR_METHOD_NOT_ALLOWED);
            return;
        }

        final String requestContent;
        try {
            final InputStream inStream = request.getEntity().getStream();
            requestContent = IOUtils.toString(inStream);
        } catch (IOException e) {
            final String message = "Process failed: " + e.getMessage();
            response.setStatus(Status.SERVER_ERROR_INTERNAL, message);
            LOGGER.log(Level.SEVERE, message, e);
            return;
        }

        final InputStream zip = getClass().getResourceAsStream("/dummy.zip");

        JSONObject jsonRequest = JSONObject.fromObject(requestContent);

        final Representation representation = new OutputRepresentation(MediaType.APPLICATION_ZIP) {
            public void write(OutputStream out) throws IOException {
                IOUtils.copy(zip, out);
            }
        };

        response.setEntity(representation);
    }
}
