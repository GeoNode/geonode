/*global define: true, requirejs:true */

requirejs.config({
    baseUrl: '/static/libs/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'status': '../js/status',
        'templates': '../js/templates'
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
