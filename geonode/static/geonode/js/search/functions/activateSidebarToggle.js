import PubSub from "app/utils/pubsub";

export default () => {
  $("nav a.toggle-nav").click(function navToggle(e) {
    e.preventDefault();
    PubSub.publish("sidebarToggle");
    if (
      $(this)
        .parents("h4")
        .siblings(".nav")
        .is(":visible")
    ) {
      $(this)
        .parents("h4")
        .siblings(".nav")
        .slideUp();
      $(this)
        .find("i")
        .attr("class", "fa fa-chevron-right");
    } else {
      $(this)
        .parents("h4")
        .siblings(".nav")
        .slideDown();
      $(this)
        .find("i")
        .attr("class", "fa fa-chevron-down");
    }
  });
};
