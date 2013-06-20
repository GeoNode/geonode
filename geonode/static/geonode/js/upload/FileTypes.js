/*globals define: true */

define(['./FileType'], function (FileType) {
    'use strict';
    return {
        SHP: new FileType({
            name: 'ESRI Shapefile',
            format: 'vector',
            main: 'shp',
            requires: ['shp', 'prj', 'dbf', 'shx']
        }),
        TIF: new FileType({
            name: 'GeoTiff File',
            format: 'raster',
            main: 'tif',
            requires: ['tif']
        }),
        TIFF: new FileType({
            name: 'GeoTiff File',
            format: 'raster',
            main: 'tiff',
            requires: ['tiff']
        }),
        // These types only supported by importer based Uplaod
        CSV: new FileType({
            name: 'Comma Separated File',
            format: 'vector',
            main: 'csv',
            requires: ['csv']
        }),
        KML: new FileType({
            name: 'Google Earth KML',
            format: 'vector',
            main: 'kml',
            requires: ['kml']
        }),
        ZIP: new FileType({
            name: 'Zip Archives',
            format: 'archive',
            main: 'zip',
            requires: ['zip']
        })
    };
});
