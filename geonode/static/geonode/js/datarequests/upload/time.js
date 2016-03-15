/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/lib/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'upload': '../../geonode/js/datarequests/upload',
        'templates': '../../geonode/js/datarequests/templates'
    }
});

define(['upload/upload','upload/common'], function (upload, common) {
    'use strict';

    var doTime = function (event) {
        var form = $("#timeForm");
        $.ajax({
           type: "POST",
           url: '/upload/time',
           data: form.serialize(), // serializes the form's elements.
           success: function(data)
           {
               if('redirect_to' in data) {
                    common.make_request({
                        url: data.redirect_to,
                        async: false,
                        failure: function (resp, status) {common.logError(resp); },
                        success: function (resp, status) {
                            window.location = resp.url;
                        }
                    });
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
