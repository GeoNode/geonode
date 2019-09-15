/*global $:true, define: true  */


define(['jquery', 'status/UploadSession'], function ($, UploadSession) {
    'use strict';

    var initialize, get_session, load_sessions;


    get_session = function (element) {
        var tr = $(element).parent().parent();
        return tr.data('session');
    };


    load_sessions = function (url) {
        var tbody = $('#session-table').find('tbody').first();
        tbody.empty();

        $.ajax({url: '/data/upload/sessions/'}).done(function (sessions) {
            $.each(sessions, function (idx, s) {
                var session = new UploadSession(s),
                    tr = session.formatTr();
                tr.appendTo(tbody);
            });
        });
    };


    initialize = function (options) {
        var delete_sessions,
            set_permissions,
            find_selected_layers;


        find_selected_layers = function (table) {
            var inputs = table.find('input:checkbox:checked'),
                res = [],
                session,
                i,
                length = inputs.length;

            for (i = 0; i < length; i += 1) {
                session = get_session(inputs[i]);
                res.push(session);
            }
            return res;
        };

        delete_sessions = function (event) {
            var table = $(options.table_selector),
                sessions = find_selected_layers(table);
            console.log(sessions);
            $.each(sessions, function (idx, session) {
                session.delete();
            });
        };

        set_permissions = function (event) {
        };


        load_sessions(options.status_url);

        $(options.delete_selector).on('click', delete_sessions);
        $(options.permission_selector).on('click', set_permissions);
    };

    return {
        initialize: initialize
    };

});