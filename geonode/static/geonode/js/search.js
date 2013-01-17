/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/libs/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'templates': '../js/templates'
    }
});

requirejs(['jquery', 'underscore', 'text!../../geonode/js/templates/search.html', 'jquery.timeago'],
function($, _, tmpl, timeago){

    $(function() {
        $('body').append(tmpl);

        $("form.geonode-search").submit(function(e) {
            e.preventDefault();
            var url = $(this).data("search-api");
            var table = $(this).data("results-table");
            var query = $(this).find("input[name=q]").val();

            // Empty results
            $(table).find("tbody").empty();

            // Get results from API
            $.getJSON(url, { q: query }, function(json) {
                if (json["total"] < 1) {
                    $(table).find("tbody:last").append($("#searchNoResultsTemplate").html());
                } else {
                    // Compile template used to render search rows
                    var _resultRow = _.template($("#searchResultsRowTemplate").html());
                    $.each(json.results, function(i, row){
                        var results = _resultRow(row);
                        $(table).find("tbody:last").append(results).find("abbr.timeago").timeago();
                    });
                }
            });
        });

        // Grab url params for initial search
        var urlParams = {};
        (function () {
            var e,
                a = /\+/g,  // Regex for replacing addition symbol with a space
                r = /([^&=]+)=?([^&]*)/g,
                d = function (s) { return decodeURIComponent(s.replace(a, " ")); },
                q = window.location.search.substring(1);

            while (e = r.exec(q))
               urlParams[d(e[1])] = d(e[2]);
        })();
        if (urlParams["q"]) {
          $("input[name=q]").val(urlParams["q"]);
        }
        $("form.geonode-search").submit();

        //Handle the new map button
        $("#newmap").submit(function(e) {
            var selected = $(".asset-selector:checked");
            $.each(selected, function(index, value) {
              var el = $(value);
              $("<input>").attr({
                type: "hidden",
                name: "layer",
                value: el.data("name")
              }).appendTo("#newmap");
              console.log(this);
            });
        });
    });


});
