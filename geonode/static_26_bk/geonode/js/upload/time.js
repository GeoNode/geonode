/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/lib/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'upload': '../../geonode/js/upload',
        'templates': '../../geonode/js/templates'
    }
});

define(['upload/upload','upload/common', 'upload/LayerInfo'], function (upload, common, LayerInfo) {
    'use strict';

    var doTime = function (event) {
        var form = $("#timeForm");
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
                    if (resp.status === "pending") {
                        setTimeout(function() {
                            makeRequest(data);
                        }, 1000);
                        return;
                    }
                    window.location = resp.url;
                }
            });
        };

      var params = common.parseQueryString(document.location.search);
      var url = '/upload/time'
      if ('id' in params){
        url = updateUrl(url, 'id', params.id);
      }
        $.ajax({
           type: "POST",
           url: url,
           data: form.serialize(), // serializes the form's elements.
           success: function(data)
           {
               if('redirect_to' in data) {
                 makeRequest(data);
                } else if ('url' in data) {
                    window.location = data.url;
                } else {
                    common.logError("unexpected response");
                }
           },
           error: function (resp, status) {
                common.logError(resp);
           }
        });
        return false;
    };

    $(function () {
        $("#next").on('click', doTime);
        $("#DISCRETE_INTERVAL,#CONTINUOUS_INTERVAL").on('change',function(ev) {
            $("#precision").show();
        });
        $("#LIST").on('change',function(ev) {
            $("#precision").hide().find("input").val(null);
        });
    });

});
