/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/lib/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'upload': '../../geonode/js/datarequests/upload',
        'templates': '../../geonode/js/templates',
    }
});

define(['upload/upload'], function (upload) {
    'use strict';

    $(function () {
        $("#next").on('click', upload.doSrs);
    });
});
