$(function() {
$(".announcement").find(".close").on("click", function (e) {
    url = $(e.target).data('dismiss-url');

    $.ajax({
          type: "POST",
          url: url
        })
    });
});
