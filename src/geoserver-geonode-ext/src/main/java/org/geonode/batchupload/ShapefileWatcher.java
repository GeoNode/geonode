package org.geonode.batchupload;

import org.geonode.http.GeoNodeHTTPClient;

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
