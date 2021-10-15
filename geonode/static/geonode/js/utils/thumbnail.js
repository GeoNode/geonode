/*
This is only used by metadata wizard.
The other pages will use the implementation provided by the specific client (MapStore)
 */
window.getThumbnailOptions = function(){
    // (west, east, south, north, CRS)
    if (typeof(olMap) == 'undefined') {
        return null;
    }
    var bbox = olMap.getExtent();
    var body = {
        srid: 'EPSG:3857',
        bbox: [bbox.left, bbox.right, bbox.bottom, bbox.top]
    };
    return body;
}

var createMapThumbnail = function(obj_id) {
    if (typeof(thumbnailUpdateUrl) == 'undefined') {
        console.error("Missing required variables");
        return true;
    }

    var body = getThumbnailOptions()
    if (body == undefined) {
        console.error("Thumbnail body undefined");
        return false;
    }
    $.ajax({
        type: "POST",
        contentType: "application/json",
        url: thumbnailUpdateUrl,
        data: JSON.stringify(body),
        async: true,
        cache: false,
        beforeSend: function () {
            // Handle the beforeSend event
            try {
                $("#_thumbnail_processing").modal("show");
            } catch (err) {
                console.log(err);
            }
        },
        complete: function () {
            // Handle the complete event
            try {
                $("#_thumbnail_processing").modal("hide");
            } catch (err) {
                console.log(err);
            }
        },
        success: function (data, status, jqXHR) {
            try {
                var title = "";
                var body = data.message;
                if (data.success || status === 'success') {
                    title = "OK";
                } else {
                    title = "Warning";
                }
                $("#_thumbnail_feedbacks").find('.modal-title').text(title);
                $("#_thumbnail_feedbacks").find('.modal-body').text(body);
                $("#_thumbnail_feedbacks").modal("show");
            } catch (err) {
                console.log(err);
            } finally {
                return true;
            }
        },
        error: function (jqXHR, textStatus) {
            try {
                if (textStatus === 'timeout') {
                    $("#_thumbnail_feedbacks").find('.modal-title').text('Timeout');
                    $("#_thumbnail_feedbacks").find('.modal-body').text('Failed from timeout: Could not create Thumbnail');
                    $("#_thumbnail_feedbacks").modal("show");
                } else {
                    $("#_thumbnail_feedbacks").find('.modal-title').text('Error: ' + textStatus);
                    $("#_thumbnail_feedbacks").find('.modal-body').text('Could not create Thumbnail');
                    $("#_thumbnail_feedbacks").modal("show");
                }
            } catch (err) {
                console.log(err);
            } finally {
                return true;
            }
        },
    });
    return true;
};
