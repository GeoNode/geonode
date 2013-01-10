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
        upload.initialize({
            form: '#file-uploader',
            file_queue: '#file-queue',
            upload_button: '#upload-button'
        });
    });

});
