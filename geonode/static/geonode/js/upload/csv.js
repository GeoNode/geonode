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

define(['underscore',
        'upload/common',
        'upload/LayerInfo',
        'text!templates/upload.html'], function (_, common, LayerInfo, csv_template) {

    'use strict';
    $('body').append(csv_template);

    $(function () {
        // Re-use the LayerInfo object to asynchronously save the new csv and present the progress to the user.
        var lyr = new LayerInfo({element:$("#csv-status"), name:"file", type:'csv', files:{csv:{name:'file.csv'}}});

        $("#upload-csv-submit").on('click', function(){
            common.make_request({
                type:'POST',
                url:'/upload/csv',
                data:$("#csvForm").serialize(),
                success: function (resp, status) {
                    lyr.doFinal(resp);
                },
                failure: function (resp, status) {
                    lyr.markError(resp.statusText, status);
                }

            });
        });
    });
});
