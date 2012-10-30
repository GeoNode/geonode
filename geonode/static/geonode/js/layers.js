$(function() {
    $("[data-viewby]").each(function() {
        $(this).find("nav.viewby a."+$(this).data("viewby")).addClass("active");
    });
    $(".viewby a").click(function(e) {
        e.preventDefault();
        if ($(this).not(".active").size()) {
            $(".tab-content .tab-pane").addClass(
                $(this).attr("class")
            ).removeClass(
                $(this).siblings("a").removeClass("active").attr("class")
            );
        }
        $(this).addClass("active");
        setContentWidth();
    });
    $("#slide-pane a.toggle-pane").click(function(e) {
        e.preventDefault();
        var span$ = $("#slide-pane").parents(".span4");
        if(!span$.is('.hidden')) {
            span$.addClass("hidden").animate({
                marginLeft: "-310px"
            }, 500, function() {
                setContentWidth();
            });
            $(this).find("i").attr("class", "icon-chevron-right");
        } else {
            span$.removeClass("hidden").animate({
                marginLeft: "0px"
            }, 500, function() {
                setContentWidth();
            });
            $(this).find("i").attr("class", "icon-chevron-left");
        }
    });
    $("nav a.toggle-nav").click(function(e) {
        e.preventDefault();
        if ($(this).parents("h2").siblings(".nav").is(":visible")) {
            $(this).parents("h2").siblings(".nav").slideUp();
            $(this).find("i").attr("class", "icon-chevron-right");
        } else {
            $(this).parents("h2").siblings(".nav").slideDown();
            $(this).find("i").attr("class", "icon-chevron-down");
        }
    });
});

function setContentWidth() {
    var lm = parseInt($("#slide-pane").parents(".span4").css("marginLeft").replace("px", "")) + 51;
    var w = $("#contain-slider").width() - ($("#slide-pane").outerWidth() + lm);
    $(".tab-content").css('width', w + "px");
}