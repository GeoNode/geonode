package org.geonode.rest;

import org.restlet.Restlet;
import org.restlet.data.MediaType;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.StringRepresentation;

import org.geoserver.catalog.Catalog;
import org.geoserver.platform.GeoServerResourceLoader;
import org.geoserver.rest.RestletException;

public class ProcessRestlet extends Restlet {
    public void handle(Request request, Response response) {
        response.setEntity(new StringRepresentation("Hello Rest", MediaType.TEXT_PLAIN));
    }
}
