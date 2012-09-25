$(function () {
    var hasMore = parseInt($(".pages .current.page").html()) < parseInt($(".pages .page_total").html()),
    $loading = $("<div class='loading'><p>Loading more items&hellip;</p></div>"),
    $pages = $(".pages");
    opts = {
        offset: '100%'
    };

    if (hasMore && !$("html.ie8").size()) {
        $pages.children().hide();
        $pages.waypoint(function(event, direction) {
            $pages.waypoint('remove');
            $pages.before($loading);
            $.get($('a.more').attr('href'), function(data) {
                var $data = $(data);
                $('.tab-pane.active').append($data.find('article'));
                $loading.detach();
                if ($data.find(".more").size()) {
                    $('.more').replaceWith($data.find('.more'));
                    $pages.waypoint(opts);
                }
            });
        }, opts);

    }
});
$.urlParam = function(name){
    if (window.location.href.search(name) != -1) {
        var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
        return results[1];
    } else return 0;
}