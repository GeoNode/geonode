package org.geonode.rest.batchdownload;

import javax.xml.namespace.QName;

import org.geoserver.data.test.MockData;

class BatchDownloadTestData {

    public static final QName VECTOR_LAYER = MockData.DIVIDED_ROUTES;

    public static final QName RASTER_LAYER = MockData.TASMANIA_DEM;

    public static final String RESTLET_BASE_PATH = "/rest/process/batchDownload";

    public static final String RASTER_LAYER_NAME = RASTER_LAYER.getPrefix() + ":"
            + RASTER_LAYER.getLocalPart();

    public static final String VECTOR_LAYER_NAME = VECTOR_LAYER.getPrefix() + ":"
            + VECTOR_LAYER.getLocalPart();

    public static final String VECTOR_LAYER_REQUEST_NO_METADATA = "{"
            + "map:{title:'fake Map', abstract:'test request for a vector layer', author:'myself'}, "
            + " layers:[{name:'"
            + VECTOR_LAYER_NAME
            + "', service:'WFS', metadataURL:'', serviceURL='http://localhost/it/doesnt/matter/so/far'}]}";

    public static final String RASTER_LAYER_REQUEST_NO_METADATA = "{"
            + "map:{title:'fake Map', abstract:'Test request for a raster layer', author:'myself'}, "
            + " layers:[{name:'"
            + RASTER_LAYER_NAME
            + "', service:'WCS', metadataURL:'', serviceURL='http://localhost/it/doesnt/matter/so/far'}]}";

    public static final String VECTOR_AND_RASTER_REQUEST_NO_METADATA = "{"
            + "map:{title:'fake Map', abstract: 'test request containing a raster and a vector layer', author:'myself'}, "
            + " layers:[{name:'"
            + VECTOR_LAYER_NAME
            + "', service:'WFS', metadataURL:'', serviceURL='http://localhost/it/doesnt/matter/so/far'},"
            + "{name:'"
            + RASTER_LAYER_NAME
            + "', service:'WCS', metadataURL:'', serviceURL='http://localhost/it/doesnt/matter/so/far'}"
            + "]}";

    public static final String VECTOR_AND_RASTER_REQUEST_WITH_METADATA = "{"
            + "map:{title:'fake Map', abstract: 'test request containing a raster and a vector layer', author:'myself'}, "
            + " layers:[{name:'"
            + VECTOR_LAYER_NAME
            + "', service:'WFS', metadataURL:'"
            + BatchDownloadTestData.class.getResource("test-data/vector_layer_metadata.xml")
                    .toExternalForm()
            + "', serviceURL='http://localhost/it/doesnt/matter/so/far'},"
            + "{name:'"
            + RASTER_LAYER_NAME
            + "', service:'WCS', metadataURL:'"
            + BatchDownloadTestData.class.getResource("test-data/raster_layer_metadata.xml")
                    .toExternalForm() + "', serviceURL='http://localhost/it/doesnt/matter/so/far'}"
            + "]}";
}
