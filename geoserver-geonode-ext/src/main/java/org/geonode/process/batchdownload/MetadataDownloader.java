package org.geonode.process.batchdownload;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.URLConnection;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.geoserver.rest.util.IOUtils;
import org.geotools.util.logging.Logging;

class MetadataDownloader {

    private static final Logger LOGGER = Logging.getLogger(MetadataDownloader.class);

    public byte[] download(final URL metadataURL) throws IOException {
        if (LOGGER.isLoggable(Level.FINE)) {
            LOGGER.fine("Opening connection to metadata record at " + metadataURL.toExternalForm());
        }
        URLConnection connection = metadataURL.openConnection();
        LOGGER.fine("Connection to metadata record open");

        InputStream inputStream = connection.getInputStream();
        ByteArrayOutputStream contents = new ByteArrayOutputStream();

        boolean closeInput = true;
        boolean closeOutput = false;
        IOUtils.copyStream(inputStream, contents, closeInput, closeOutput);

        return contents.toByteArray();
    }
}
