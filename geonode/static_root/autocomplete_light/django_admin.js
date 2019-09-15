$(document).ready(function() {

    $('.autocomplete-light-widget').on('initialize', function() {
        /*
        Set .change-related link when the admin loads, because it's apparently
        unable to do it server side on initial rendering, not sure why, would
        love to know !

        For django 1.8 admin support.
        */
        var value = $(this).find('select').val();

        if (value !== undefined && value !== null) {
            var next = $(this).next();
            var template = next.attr('data-href-template');

            if (template && next.is('.change-related')) {
                next.attr('href', template.replace('__fk__', value));
            }
        }
    });

    $(document).bind('widgetSelectChoice', function(e, choice, widget) {
        /*
        Set the .change-related link when an item is selected.

        For django 1.8 admin support.
        */
        var next = widget.widget.next();
        var template = next.attr('data-href-template');

        if (template && next.is('.change-related')) {
            next.attr('href', template.replace('__fk__', widget.getValue(choice)));
        }
    });

    $(document).bind('widgetDeselectChoice', function(e, choice, widget) {
        /*
        Unset the .change-related link when an item is selected.

        For django 1.8 admin support.
        */
        var next = widget.widget.next();
        var template = next.attr('data-href-template');

        if (template && next.is('.change-related') && next.attr('href')) {
            next.removeAttr('href');
        }
    });

});
