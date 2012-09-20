$(function () {
    var hasMore = parseInt($(".pages .current.page").html()) < parseInt($(".pages .page_total").html());
    if (hasMore && !$("html.ie8").size()) {
        $('.pages').hide().after('<div class="loadmore"><a href="#">Show More <i class="icon-chevron-down"></i></a></div>');
        $('.loadmore a').click(function (e) {
            e.preventDefault();
            $('.loadmore').addClass('loading');
            var nextpage = parseInt($(".pages:last .current.page").html()) + 1;
            if (nextpage <= parseInt($(".pages:last .page_total").html())) {
                $.ajax({
                    url: window.location.pathname+'?page='+nextpage+($.urlParam('q') ? '&q='+$.urlParam('q') : ''),
                    context: $('.tab-pane'),
                    dataType: 'html',
                    success: function (data) {
                        $(".loadmore").removeClass('loading').before(
                            $("<div class=\"loaddata\" style=\"display:none\">"+data+"</div>")
                        );
                        $(".tab-pane").append($(".loaddata").find("article"));
                        $('.viewcount span:eq(0)').html($(".tab-pane > article").size());
                        $(".pages").html($(".loaddata").find(".pages").html());
                        var pagination = $(".pages:last");
                        if (parseInt(pagination.find('.current.page').html()) >= parseInt(pagination.find('.page_total').html()))
                            $('.loadmore a').hide();
                        pagination.hide();
                        $(".loaddata").remove();
                    }
                });
            }
        });
    }
});
$.urlParam = function(name){
    if (window.location.href.search(name) != -1) {
        var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
        return results[1];
    } else return 0;
}