export default (() => {
  $("#text_search_input").yourlabsAutocomplete({
    url: AUTOCOMPLETE_URL_RESOURCEBASE,
    choiceSelector: "span",
    hideAfter: 200,
    minimumCharacters: 1,
    placeholder: gettext("Enter your text here ..."),
    autoHilightFirst: false
  });

  $("#text_search_input").keypress(e => {
    if (e.which === 13) {
      $("#text_search_btn").click();
      $(".yourlabs-autocomplete").hide();
    }
  });

  $("#text_search_input").bind(
    "selectChoice",
    (e, choice, text_autocomplete) => {
      if (choice[0].children[0] == undefined) {
        $("#text_search_input").val($(choice[0]).text());
        $("#text_search_btn").click();
      }
    }
  );

  $("#text_search_btn").click(function() {
    if (AUTOCOMPLETE_URL_RESOURCEBASE == "/autocomplete/ProfileAutocomplete/")
      // a user profile has no title; if search was triggered from
      // the /people page, filter by username instead
      var query_key = "username__icontains";
    else console.log("search key", $("#text_search_input").data());
    var query_key =
      $("#text_search_input").data("query-key") || "title__icontains";
    $scope.query[query_key] = $("#text_search_input").val();
    query_api($scope.query);
  });
})();
