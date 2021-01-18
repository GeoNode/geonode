/*globals define: true */

define(['./FileType'], function (FileType) {
    'use strict';
    var file_types = {};
    file_types['SHP'] = new FileType({
            name: gettext('ESRI Shapefile'),
            format: 'vector',
            main: 'shp',
            requires: ['shp', 'prj', 'dbf', 'shx']
        });
    file_types['ASCII'] = new FileType({
            name: gettext('ASCII Text File'),
            format: 'raster',
            main: 'asc'
        });
    file_types['TIF'] = new FileType({
            name: gettext('GeoTIFF'),
            format: 'raster',
            main: 'tif'
        });
    file_types['TIFF'] = new FileType({
            name: gettext('GeoTIFF'),
            format: 'raster',
            main: 'tiff'
        });
    // requires geonode.importer
    file_types['CSV'] = new FileType({
            name: gettext('Comma Separated Value'),
            format: 'vector',
            main: 'csv'
        });
    file_types['KML'] = new FileType({
            name: gettext('Google Earth KML'),
            format: 'vector',
            main: 'kml'
        });
    file_types['KML_GROUND_OVERLAY'] = new FileType({
            name: gettext('Google Earth KML with a GroundOverlay'),
            format: 'raster',
            main: 'kml',
            aux: ['png', 'gif', 'tiff', 'tif', 'jpg']
    });
    file_types['KMZ'] = new FileType({
            name: gettext('Google Earth KMZ'),
            format: 'archive',
            main: 'kmz'
    });
    file_types['GEOJSON'] = new FileType({
            name: gettext('GeoJSON'),
            format: 'vector',
            main: 'geojson'
        });
    file_types['ZIP'] = new FileType({
            name: gettext('Zip Archive'),
            format: 'archive',
            main: 'zip'
        });
    // requires geonode.importer + gs gdal ext
    file_types['IMG'] = new FileType({
            name: gettext('ERDAS Imagine'),
            format: 'raster',
            main: 'img'
        });
    file_types['NTF'] = new FileType({
            name: gettext('National Imagery Transmission Format'),
            format: 'raster',
            main: 'ntf'
        });
    file_types['NITF'] = new FileType({
            name: gettext('National Imagery Transmission Format'),
            format: 'raster',
            main: 'nitf'
        });
    for (var i = 0; i < 10; i++) {
        file_types['CIB_I4' + i] = new FileType({
            name: gettext('Controlled Image Base-1 Meter'),
            format: 'raster',
            main: 'i4' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['CIB_I2' + i] = new FileType({
            name: gettext('Controlled Image Base-5 Meter'),
            format: 'raster',
            main: 'i2' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['CIB_I1' + i] = new FileType({
            name: gettext('Controlled Image Base-10 Meter'),
            format: 'raster',
            main: 'i1' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['GNC_GN' + i] = new FileType({
            name: gettext('CADRG-Global Navigation Chart'),
            format: 'raster',
            main: 'gn' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['JNC_JN' + i] = new FileType({
            name: gettext('CADRG-Jet Navigation Chart'),
            format: 'raster',
            main: 'jn' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['ONC_ON' + i] = new FileType({
            name: gettext('CADRG-Operational Navigation Chart'),
            format: 'raster',
            main: 'on' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['TPC_TP' + i] = new FileType({
            name: gettext('CADRG-Tactical Pilotage Chart'),
            format: 'raster',
            main: 'tp' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['JOG_JA' + i] = new FileType({
            name: gettext('CADRG-Joint Operations Graphic'),
            format: 'raster',
            main: 'ja' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['TLM_TC' + i] = new FileType({
            name: gettext('CADRG-Topographic Line Map 100K'),
            format: 'raster',
            main: 'tc' + i
        });
    };
    for (var i = 0; i < 10; i++) {
        file_types['TLM_TL' + i] = new FileType({
            name: gettext('CADRG-Topographic Line Map 50K'),
            format: 'raster',
            main: 'tl' + i
        });
    };
    // requires gdal to be built with mrsid and jp2
    file_types['JP2'] = new FileType({
            name: gettext('JPEG2000'),
            format: 'raster',
            main: 'jp2'
        });
    file_types['SID'] = new FileType({
            name: gettext('MrSID-Multi-resolution Seamless Image Database'),
            format: 'raster',
            main: 'sid'
        });
    file_types['XML'] = new FileType({
            name: gettext('XML Metadata File'),
            format: 'metadata',
            main: 'xml'
        });
    // Style Layer Descriptors
    file_types['SLD'] = new FileType({
            name: gettext('Style Layer Descriptor'),
            format: 'metadata',
            main: 'sld'
        });
    // Plain Images
    file_types['JPEG'] = new FileType({
            name: gettext('JPEG'),
            format: 'image',
            main: 'jpg'
        });
    file_types['PNG'] = new FileType({
            name: gettext('PNG'),
            format: 'image',
            main: 'png'
        });
    file_types['GIF'] = new FileType({
            name: gettext('GIF'),
            format: 'image',
            main: 'gif'
        });

    return file_types;
});
