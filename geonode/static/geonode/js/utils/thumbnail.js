var createMapThumbnail = function(obj_id) {
    // var xmap = ($('.olMapViewport')[0] != undefined ? $('.olMapViewport') : $('#embedded_map'));
    var xmap = ($('.olMapViewport')[0] != undefined ? $('.olMapViewport') : $('#embedded_map'));

    if ($('#preview_map')[0] != undefined) {
        if ($('#preview_map').css('display') != 'none' &&
                $('.olMapViewport')[0] != undefined) {
            xmap = $('.olMapViewport');
        } else {
            xmap = $('#preview_image');
        }
    }

    height = xmap.height();
    width = xmap.width();
    var map = xmap.clone();
    map.find('*').each(function(i) {
        e = $(this);
        if(e.css('display') === 'none' || (e.attr("class") !== undefined && (e.attr("class").indexOf('olControl') >= 0 || e.attr("class").indexOf('ol-overlaycontainer') >= 0 || e.attr("class").indexOf('x-') >= 0))) {
            e.remove();
        } else if (e.attr('src') === '/static/geoexplorer/externals/ext/resources/images/default/s.gif') {
            e.remove();
        } else {
            e.removeAttr("id");
        }
    });

    var url = window.location.pathname.replace('/view', '');
        url = url.replace('/edit', '');
        url = url.replace('/metadata', '');
        url = url.replace('/metadata#', '');

    if (typeof obj_id != 'undefined' && url.indexOf('new')){
        url = url.replace('new', obj_id);
    }

    url+= '/thumbnail';
    var body = ("<div style='height:" + height + "px; width: " + width + "px;'>" + map.html() + "</div>");

    $.ajax({
        type: "POST",
        url: url,
        data: body,
        async: false,
        cache: false,
        success: function(data, status, jqXHR) {
            try {
                $("#_thumbnail_feedbacks").find('.modal-title').text(status);
                $("#_thumbnail_feedbacks").find('.modal-body').text(data);
                $("#_thumbnail_feedbacks").modal("show");
            } catch(err) {
                console.log(err);
            } finally {
                return true;
            }
        }
    });
    return true;
};
