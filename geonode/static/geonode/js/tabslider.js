$(function() {
    $("#slide-pane a.toggle-pane").click(function(e) {
        e.preventDefault();
        if(!$("#slide-pane").is('.hidden')) {
            $("#slide-pane").addClass("hidden").animate({
                marginLeft: "-310px"
            }, 500);
            $(this).find("i").attr("class", "icon-chevron-right");
            /*$(".tab-content").animate({
                width: "100%"
            }, 500);*/
        } else {
            $("#slide-pane").removeClass("hidden").animate({
                marginLeft: "0px"
            }, 500);
            $(this).find("i").attr("class", "icon-chevron-left");
        }
    });
    $("nav a.toggle-nav").click(function(e) {
        e.preventDefault();
        if ($(this).parents("h2").siblings(".nav").is(":visible")) {
            $(this).parents("h2").siblings(".nav").slideUp();
            $(this).find("i").attr("class", "icon-chevron-left");
        } else {
            $(this).parents("h2").siblings(".nav").slideDown();
            $(this).find("i").attr("class", "icon-chevron-down");
        }
    });
});