/*global define: true, $:true */

define(function () {
    'use strict';

    var UploadSession = function (options) {
        this.name = null;
        this.id = null;
        this.layer_name = null;
        this.layer_id = null;
        this.state = null;
        this.url = null;
        this.date = null;

        $.extend(this, options || {});
    };


    UploadSession.prototype.handle_edit = function (event) {
        var target = $(event.target),
            session = target.data('session');
        console.log(session);
    };


    UploadSession.prototype.wrap_value = function (value) {
        var td = $('<td/>');

        if ((typeof value === 'object') && (value)) {
            value.appendTo(td);
        } else {
            $('<p/>', {text: value}).appendTo(td);
        }
        return td;
    };

    // TODO, use a template for this
    UploadSession.prototype.formatTr = function () {
        var tr = $('<tr />'),
            input,
            name,
            div,
            a;
        tr.data('session', this);
        input = $('<input/>', {type: 'checkbox'});
        this.wrap_value(input).appendTo(tr);

        a = $('<a/>', {text: 'Edit'});
        a.on('click', this.handle_edit);
        if (this.url) {
            this.wrap_value($('<a/>', {text: this.layer_name, href: this.url}))
                .appendTo(tr);
        } else {
            this.wrap_value(this.layer_name).appendTo(tr);
        }
        this.wrap_value(a).appendTo(tr);
        this.wrap_value(this.date).appendTo(tr);
        this.wrap_value(this.state).appendTo(tr);
        this.element = tr;
        return tr;
    };

    return UploadSession;

});
