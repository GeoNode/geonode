/*globals define: true, requirejs: true */

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

define(['upload/upload',
        'upload/common',
        'upload/LayerInfo'], function (upload, common, LayerInfo) {
    'use strict';

    var doSrs = function (event) {
        var form = $("#crsForm");
        $('#next-spinner').removeClass('hide');

        function makeRequest(data) {
            common.make_request({
                url: data.redirect_to,
                async: false,
                failure: function (resp, status) {
                    common.logError(resp);
                    $('#next-spinner').addClass('hide');
                },
                success: function (resp, status) {
                    if (resp.status) {
                        if (resp.status === 'error') {
                            self.polling = false;
                            common.logError(resp.error_msg);
                            $('#next-spinner').addClass('hide');
                        } else if (resp.status === 'pending') {
                            setTimeout(function() {
                                makeRequest(resp);
                            }, 5000);
                            return;
                        } else if (resp.status === 'incomplete') {
                            if('redirect_to' in resp && resp.redirect_to) {
                                self.polling = false;
                                window.location = resp.redirect_to;
                            } else if ('url' in resp && resp.url) {
                                self.polling = false;
                                window.location = resp.url;
                            } else {
                                common.logError("unexpected response");
                                $('#next-spinner').addClass('hide');
                            }
                        } else if (resp.status === 'finished') {
                            self.polling = false;
                            window.location = resp.url;
                        }
                    } else {
                         if('redirect_to' in resp && resp.redirect_to) {
                             makeRequest(resp);
                         } else if ('url' in resp && resp.url) {
                             self.polling = false;
                             window.location = resp.url;
                         } else {
                             common.logError("unexpected response");
                             $('#next-spinner').addClass('hide');
                         }
                     }
                }
            });
        };

      var params = common.parseQueryString(document.location.search);
      var url = siteUrl + 'upload/srs'
      if ('id' in params){
        url = updateUrl(url, 'id', params.id);
      }
        $.ajax({
           type: "POST",
           url: url,
           data: form.serialize(), // serializes the form's elements.
           success: function(data)
           {
               if (data.status) {
                   if (data.status === 'error') {
                       self.polling = false;
                       common.logError(data.error_msg);
                       $('#next-spinner').addClass('hide');
                   } else if (data.status === 'pending' ||
                            data.status === 'incomplete') {
                       makeRequest(data);
                   }
               } else {
                    if('redirect_to' in data && data.redirect_to) {
                        makeRequest(data);
                    } else if ('url' in data && data.url) {
                        self.polling = false;
                        window.location = data.url;
                    } else {
                        common.logError("unexpected response");
                        $('#next-spinner').addClass('hide');
                    }
                }
           },
           error: function (resp, status) {
                common.logError(resp);
                $('#next-spinner').addClass('hide');
           }
        });
        return false;
    };

    $(function () {
        $("#next").on('click', doSrs);
    });

});
