package org.geonode.rest;

import org.geoserver.catalog.Catalog;

import java.io.IOException;
import java.io.InputStream;
import java.util.logging.Level;
import java.util.logging.Logger;
import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;
import org.apache.commons.io.IOUtils;
import org.geotools.process.ProcessException;
import org.restlet.data.MediaType;
import org.restlet.data.Method;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.Representation;
import org.restlet.resource.StringRepresentation;
import org.restlet.Restlet;

public class DownloadLauncherRestlet extends Restlet {
    private Catalog catalog;
    private static Logger LOGGER = org.geotools.util.logging.Logging.getLogger("org.geonode.rest");

    public DownloadLauncherRestlet(final Catalog catalog) {
        this.catalog = catalog;
    }

    public void handle(Request request, Response response) {
        if (!request.getMethod().equals(Method.POST)) {
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

        JSONObject jsonRequest = JSONObject.fromObject(requestContent);

        final JSONObject responseData = new JSONObject();
        responseData.put("id", 12);
        responseData.put("status", "WAITING");
        responseData.put("statusMessage", "Process is waiting...");

        final String jsonStr = responseData.toString(0);
        final Representation representation =
            new StringRepresentation(jsonStr, MediaType.APPLICATION_JSON);

        response.setEntity(representation);
    }
}
