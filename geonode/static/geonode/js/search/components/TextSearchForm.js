import PubSub from "pubsub-js";

const TextSearchForm = ({ url, id }) => {
  const module = {
    url,
    id,
    getForm: () => $(`#${module.id}_input`),
    getFormVal: () => module.getForm().val()
  };
  const $form = $(`#${id}_input`);
  const $btn = $(`#${id}_btn`);
  $form.yourlabsAutocomplete({
    url,
    choiceSelector: "span",
    hideAfter: 200,
    minimumCharacters: 1,
    // eslint-disable-next-line
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
      module.getForm().val($(choice[0]).text());
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
      console.log("search key", module.getForm().data());
      queryKey = module.getForm().data("query-key") || "title__icontains";
    }
    const searchVal = module.getFormVal();
    PubSub.publish("textSearchClick", {
      key: queryKey,
      val: searchVal
    });
  });
  return module;
};

export default TextSearchForm;
