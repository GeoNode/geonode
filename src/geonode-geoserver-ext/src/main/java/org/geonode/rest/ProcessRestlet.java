package org.geonode.rest;

import java.io.InputStream;
import java.io.IOException;
import java.io.OutputStream;

import org.restlet.Restlet;
import org.restlet.data.MediaType;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.OutputRepresentation;

import org.geoserver.catalog.Catalog;
import org.geoserver.platform.GeoServerResourceLoader;
import org.geoserver.rest.RestletException;

public class ProcessRestlet extends Restlet {
    public void handle(Request request, Response response) {
        response.setEntity(new OutputRepresentation(MediaType.APPLICATION_JSON) {
            public InputStream getStream() {
                return ProcessRestlet.class.getResourceAsStream("/dummy.json");
            }

            public void write(OutputStream out) throws IOException { 
                InputStream in = getStream();
                byte[] buff = new byte[1024];
                int len = 0;
                while ((len = in.read(buff)) != -1) {
                    out.write(buff, 0, len);
                }
                out.flush();
                out.close();
            }
        });
    }
}
