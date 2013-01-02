/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/libs/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'templates': '../js/templates'
    }
});

requirejs(['../js/utils', 'jquery', 'underscore', 'bootstrap/js/bootstrap', 'jquery.timeago'],
    function(util, $){
        window.gn = window.gn || {};
        $.extend(gn, {utils: util});

        $("#permission_form").submit(gn.utils.layerPermsSubmit);
    }
);
