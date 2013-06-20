/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'jquery': 'lib/js/jquery',
        'upload': 'geonode/js/upload',
        'templates': 'geonode/js/templates'
    }
});

define(['jquery', 'upload/upload'], function ($, upload) {
    'use strict';

    $(function () {
        $("#next").on('click', upload.doSrs);
    });
});
