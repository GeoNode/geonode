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
        })//,
        // CSV: new FileType({
        //     name: 'Comma Separated File',
        //     main: 'csv',
        //     requires: ['csv']
        // }),
        // ZIP: new FileType({
        //     name: 'Zip Archives',
        //     main: 'zip',
        //     requires: ['zip']
        // })
    };
});
