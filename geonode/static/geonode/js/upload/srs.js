/*globals define: true, requirejs: true */

define(['upload/upload'], function (upload) {
    'use strict';

    $(function () {
        $("#next").on('click', upload.doSrs);
    });
});
