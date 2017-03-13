var ol2_createMapThumbnail = function(obj_id) {
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

/*
 * Uses the features of Canvas to generate a thumbnail and
 * upload it to the server.
 */
var ol3_createMapThumbnail = function() {
    var canvas = $('.ol-viewport canvas');

    // first, calculate the center 'thumbnail'
    //   of the image.
    var thumb_w = 240, thumb_h = 180;
    var w = canvas.width(), h = canvas.height();
    var c_x = w/2, c_y = h/2;
    var x0 = c_x - thumb_w/2;
    var y0 = c_y - thumb_h/2;

    // then get the thumbnail from the image itself.
    var clip = canvas[0].getContext('2d').getImageData(x0,y0,thumb_w,thumb_h);

    // create a temporary canvas for the 
    //  new thumbnail.
    var thumb_canvas = $('<canvas>').appendTo('body');
    thumb_canvas[0].width = thumb_w;
    thumb_canvas[0].height = thumb_h;
    thumb_canvas[0].getContext('2d').putImageData(clip,0,0);

    // get the PNG for saving...
    var png_data = thumb_canvas[0].toDataURL('image/png');

    // and remove the element from the DOM.
    thumb_canvas.remove();

    // now, determine the URL and upload the thumbnail.
    var url = window.location.pathname.replace('/view', '');
    if (typeof obj_id != 'undefined' && url.indexOf('new')){
        url = url.replace('new', obj_id);
    }
    url+= '/thumbnail';

    $.ajax({
        type: "POST",
        url: url,
        data: png_data,
        success: function(data, status, jqXHR) {
            return true;
        }
    });
    return true;
}

var createMapThumbnail = function(obj_id) {
    // when ol-viewport is found, assume OpenLayers 3+
    if($('.ol-viewport').length > 0) {
        ol3_createMapThumbnail();
    } else {
        // default to OpenLayers 2.
        ol2_createMapThumbnail(obj_id);
    }
};
