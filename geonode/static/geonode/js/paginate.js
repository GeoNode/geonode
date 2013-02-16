var loading = "<div class='loading'><p>Loading more items&hellip;</p></div>";

$(paginate());

function paginate() {
    $(".paginate").each(function() {
        var p$ = $(this);
        var auto = p$.hasClass("paginate-auto") ? true : false,
        hasMore = parseInt(p$.find(".pagination .current.page").html()) < parseInt(p$.find(".pagination .page_total").html()),
        $pages = p$.find(".pagination");
        opts = {
            offset: '100%'
        };

        if (hasMore && !$("html.ie8").size()) {
            $pages.children().hide();
            if (auto) {
                $pages.waypoint(function(event, direction) {
                    $pages.waypoint('remove');
                    fetchMore($(this).find("a.more").get(0));
                }, opts);
            } else {
                $pages.prepend($("<a></a>", {
                    href: $pages.find("a.more").attr("href"),
                    html: "<i class=\"icon-chevron-down\"></i> Show more",
                    "class": "more"
                    }
                ).click(function(e) {
                    e.preventDefault();
                    fetchMore(this);
                }));
            }
        }
    });
}

function fetchMore(a) {
    $(a).before($(loading));
    $.ajax({
        url: $(a).attr('href'),
        context: $(a).parents(".paginate"),
        success: function(data, status, jqxhr) {
            var $data = $(data).find(".paginate");
            var articles = $data.find('.paginate-contents article');
            var more = $data.find("a.next").attr("href");
            $(this).find(".paginate-contents").append(articles).trigger("paginate.loaded", [articles]);
            $(this).find(".loading").detach();
            if (more) {
                $(this).find('.more').attr("href", more);
                if ($(this).hasClass("paginate-auto")) $(this).find(".pagination").waypoint(opts);
            } else $(this).find('.more').remove();
            rateMore();
        }
    });
}
