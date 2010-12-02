package org.geonode.batchupload;

import org.geonode.http.GeoNodeHTTPClient;

public class GeoTiffWatcher extends GeoNodeBatchUploadNotifier {

    public GeoTiffWatcher(GeoNodeHTTPClient httpClient) {
        super(httpClient);
    }

    @Override
    protected boolean canHandle(String filePath) {
        String name = filePath.toLowerCase();
        return name.endsWith(".tiff") || name.endsWith(".tif");
    }

}
