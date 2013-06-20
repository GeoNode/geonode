/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/libs/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'upload': '../../geonode/js/upload',
        'templates': '../../geonode/js/templates'
    }
});

define(['jquery', 'upload/upload'], function ($, upload) {
    'use strict';

    $(function () {
        $("#next").on('click', upload.doTime);
    });
});
