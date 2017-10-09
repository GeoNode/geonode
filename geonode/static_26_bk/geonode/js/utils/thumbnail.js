var createMapThumbnail = function(obj_id) {
    var xmap = $('.olMapViewport');
    height = xmap.height();
    width = xmap.width();
    var map = xmap.clone(); 
    map.find('*').each(function(i) {
        e = $(this);
        if(e.css('display') === 'none' || (e.attr("class") !== undefined && (e.attr("class").indexOf('olControl') >= 0 || e.attr("class").indexOf('x-') >= 0))) {
            e.remove(); 
        } else if (e.attr('src') === '/static/geoexplorer/externals/ext/resources/images/default/s.gif') {
            e.remove();
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
