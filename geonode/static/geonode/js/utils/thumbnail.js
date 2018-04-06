var createMapThumbnail = function(obj_id) {
    var xmap = $('.olMapViewport');
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

    if (typeof obj_id != 'undefined' && url.indexOf('new')){
        url = url.replace('new', obj_id);
    }

    url+= '/thumbnail';

    $.ajax({
        type: "POST",
        url: url, 
        data: ("<div style='height:" + height + "px; width: " + width + "px;'>" + map.html() + "</div>"), 
        success: function(data, status, jqXHR) {
            return true;
        }
    });
    return true;
};
