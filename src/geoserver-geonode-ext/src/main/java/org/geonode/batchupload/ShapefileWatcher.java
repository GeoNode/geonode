package org.geonode.batchupload;

import org.geonode.http.GeoNodeHTTPClient;

/**
 * GeoNode batch upload notifier that recognizes ShapeFile uploads by comparing the file extensions
 * to {@code .shp}.
 * 
 * @author groldan
 * 
 */
public class ShapefileWatcher extends GeoNodeBatchUploadNotifier {

    public ShapefileWatcher(GeoNodeHTTPClient httpClient) {
        super(httpClient);
    }

    @Override
    protected boolean canHandle(String filePath) {
        String name = filePath.toLowerCase();
        return name.endsWith(".shp");
    }

}
