/*globals define: true, requirejs: true */

requirejs.config({
  config: {
     baseUrl: siteUrl + 'static/lib/js',
     text: {
       useXhr: function (url, protocol, hostname, port) {
          // allow cross-domain requests
          // remote server allows CORS
          return true;
       }
     },
     shim: {
        'underscore': { exports: '_'}
     },
     paths: {
         'upload': '../../geonode/js/upload',
         'templates': '../../geonode/js/templates',
         'progress': 'jquery.ajax-progress'
     },
     waitSeconds: 5
  }
});

define(['upload/upload'], function (upload) {
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
