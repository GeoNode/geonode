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
        if(e.css('display') === 'none' ||
            // leaflet
            ($('.leaflet-tile-pane')[0] != undefined && e.attr("class") !== undefined &&
                ((e.attr("class").indexOf('leaflet-layer') < 0 && e.attr("class").indexOf('leaflet-tile') < 0) ||
                 e.attr("class").indexOf('x-') >= 0)) ||
            // OpenLayers
            ($('.olMapViewport')[0] != undefined && e.attr("class") !== undefined &&
                (e.attr("class").indexOf('olControl') >= 0 ||
                 e.attr("class").indexOf('olImageLoadError') >= 0 ||
                 e.attr("class").indexOf('ol-overlaycontainer') >= 0 ||
                 e.attr("class").indexOf('x-') >= 0))
        ) {
            e.remove();
        } else if (e.attr('src') !== undefined) {
            if (e.attr('src').indexOf('images/default') > 0 || e.attr('src').indexOf('default/img') > 0) {
                e.remove();
            }
            if (!e.attr('src').startsWith("http")) {
                var href = e.attr('src');
                e.attr('src', 'http:' + href);
            }
            e.css({
                "visibility":"inherit",
                "position":"absolute"
            });
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
        async: true,
        cache: false,
        beforeSend: function(){
             // Handle the beforeSend event
             try {
                 $("#_thumbnail_processing").modal("show");
             } catch(err) {
                 console.log(err);
             }
        },
        complete: function(){
             // Handle the complete event
             try {
                 $("#_thumbnail_processing").modal("hide");
             } catch(err) {
                 console.log(err);
             }
        },
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
        },
        error: function(jqXHR, textStatus){
            try {
                if(textStatus === 'timeout')
                {
                    $("#_thumbnail_feedbacks").find('.modal-title').text('Timeout');
                    $("#_thumbnail_feedbacks").find('.modal-body').text('Failed from timeout: Could not create Thumbnail');
                    $("#_thumbnail_feedbacks").modal("show");
                } else {
                    $("#_thumbnail_feedbacks").find('.modal-title').text('Error: ' + textStatus);
                    $("#_thumbnail_feedbacks").find('.modal-body').text('Could not create Thumbnail');
                    $("#_thumbnail_feedbacks").modal("show");
                }
            } catch(err) {
                console.log(err);
            } finally {
                return true;
            }
        },
        timeout: 60000 // sets timeout to 60 seconds
    });
    return true;
};
