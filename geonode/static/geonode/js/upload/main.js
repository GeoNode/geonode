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
        upload.initialize({
            form: '#file-uploader',
            dropZone: '#drop-zone',
            file_queue: '#file-queue',
            clear_button: '#clear-button',
            upload_button: '#upload-button'
        });
    });

});
