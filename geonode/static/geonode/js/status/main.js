/*global define: true, requirejs:true */

'use strict';

requirejs.config({
  config: {
     text: {
       useXhr: function (url, protocol, hostname, port) {
          // allow cross-domain requests
          // remote server allows CORS
          return true;
       }
     },
     waitSeconds: 5
  },
  baseUrl: staticUrl + 'lib/js',
  shim: {
    'underscore': { exports: '_'}
  },
  paths: {
    'upload': '../../geonode/js/upload',
    'templates': '../../geonode/js/templates',
    'progress': 'jquery.ajax-progress'
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
