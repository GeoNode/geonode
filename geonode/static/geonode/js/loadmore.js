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
                var articles = $data.find('article');
                $('.loadmore').append(articles);
                $(".loadmore").trigger("load.loadmore", [articles]);
                $loading.detach();
                if ($data.find(".more").size()) {
                    $('.more').replaceWith($data.find('.more'));
                    $pages.waypoint(opts);
                }
            });
        }, opts);

    }
});