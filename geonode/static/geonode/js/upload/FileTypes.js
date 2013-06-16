/*globals define: true */

define(['./FileType'], function (FileType) {
    'use strict';
    return {
        SHP: new FileType({
            name: 'ESRI Shapefile',
            main: 'shp',
            requires: ['shp', 'prj', 'dbf', 'shx']
        }),
        TIF: new FileType({
            name: 'GeoTiff File',
            main: 'tif',
            requires: ['tif']
        }),
        TIFF: new FileType({
            name: 'GeoTiff File',
            main: 'tiff',
            requires: ['tiff']
        }),
        // These types only supported by importer based Uplaod
        CSV: new FileType({
            name: 'Comma Separated File',
            main: 'csv',
            requires: ['csv']
        }),
        KML: new FileType({
            name: 'Google Earth KML',
            main: 'kml',
            requires: ['kml']
        }),
        ZIP: new FileType({
            name: 'Zip Archives',
            main: 'zip',
            requires: ['zip']
        })
    };
});
