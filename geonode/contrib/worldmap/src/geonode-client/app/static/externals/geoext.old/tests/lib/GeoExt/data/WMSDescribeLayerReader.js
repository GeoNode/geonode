var doc = (new OpenLayers.Format.XML).read(
    '<?xml version="1.0" encoding="UTF-8"?>'+
    '<!DOCTYPE WMS_DescribeLayerResponse SYSTEM "http://demo.opengeo.org/geoserver/schemas/wms/1.1.1/WMS_DescribeLayerResponse.dtd">'+
    '<WMS_DescribeLayerResponse version="1.1.1">'+
        '<LayerDescription name="topp:states" wfs="http://demo.opengeo.org/geoserver/wfs/WfsDispatcher?">'+
            '<Query typeName="topp:states"/>'+
        '</LayerDescription>'+
        '<LayerDescription name="topp:bluemarble" wfs="http://demo.opengeo.org/geoserver/wfs/WfsDispatcher?">'+
        '</LayerDescription>'+
    '</WMS_DescribeLayerResponse>'
);

var doc2 = (new OpenLayers.Format.XML).read(
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' +
    '<!DOCTYPE ServiceExceptionReport SYSTEM "http://mapstory.dev.opengeo.org:80/geoserver/schemas/wms/1.1.1/WMS_exception_1_1_1.dtd">' +
    ' <ServiceExceptionReport version="1.1.1" >   <ServiceException code="LayerNotDefined" locator="MapLayerInfoKvpParser">' +
    '  geonode:_map_107_annotations: no such layer on this server' +
    '</ServiceException></ServiceExceptionReport>'
);
