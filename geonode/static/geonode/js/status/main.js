/*global define: true, requirejs:true */

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

define(['jquery', 'status/status'], function ($, status) {
    'use strict';

    $(function () {
        status.initialize({
            delete_selector: '#delete',
            permission_selector: '#set-permissions',
        });
    });

});
