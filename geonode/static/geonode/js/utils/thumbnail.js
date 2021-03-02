var createMapThumbnail = function(obj_id) {
    if (typeof(thumbnailUpdateUrl) == 'undefined' || typeof(olMap) == 'undefined') {
        console.error("Missing required variables");
        return true;
    }
    // (west, east, south, north, CRS)
    var bbox = olMap.getExtent();
    var body = {
        srid: 'EPSG:3857',
        bbox: [bbox.left, bbox.right, bbox.bottom, bbox.top]
    };
    $.ajax({
        type: "POST",
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
                $("#_thumbnail_feedbacks").find('.modal-title').text(status);
                $("#_thumbnail_feedbacks").find('.modal-body').text(data);
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
