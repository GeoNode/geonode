import PubSub from "pubsub-js";

export default {
  init: ({ url, id }) => {
    const $form = $(`#${id}_input`);
    const $getForm = () => $(`#${id}_input`);
    const $btn = $(`#${id}_btn`);
    $form.yourlabsAutocomplete({
      url,
      choiceSelector: "span",
      hideAfter: 200,
      minimumCharacters: 1,
      placeholder: gettext("Enter your text here ..."),
      autoHilightFirst: false
    });

    $form.keypress(e => {
      if (e.which === 13) {
        $btn.click();
        $(".yourlabs-autocomplete").hide();
      }
    });

    $form.bind("selectChoice", (e, choice) => {
      if (choice[0].children[0] === undefined) {
        $getForm().val($(choice[0]).text());
        $btn.click();
      }
    });

    $btn.click(() => {
      let queryKey;
      if (url === "/autocomplete/ProfileAutocomplete/") {
        // a user profile has no title; if search was triggered from
        // the /people page, filter by username instead
        queryKey = "username__icontains";
      } else {
        // eslint-disable-next-line
        console.log("search key", $getForm().data());
        queryKey = $getForm().data("query-key") || "title__icontains";
      }
      const searchVal = $getForm().val();
      PubSub.publish("textSearchClick", {
        key: queryKey,
        val: searchVal
      });
    });
  }
};
