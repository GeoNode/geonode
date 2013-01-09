/*global $:true, Hogan: true, window:true */

'use strict';

var srt = Hogan.compile($("#searchResult").html());

var RelatedSearch = function () {
    this.label = $("<strong>related searches:</strong>");
    this.label.appendTo("p.related-search").hide();
    this.container = $("<ul></ul>");
    this.container.appendTo("p.related-search");
};

RelatedSearch.prototype.load = function (data) {
    $.each(data.items, function (index, item) {
        this.container.append($('<li/>', {text: item}));
        // this.container.append("<li>" + item + "</li>");
    });
};

var Keyword = function () {
    this.keywords = $("#filter-keywords label");
    this.keywords.append($('<span/>', {'class': 'count', 'text': 0}));
    // this.keywords.append(" (<span class=\"count\">0</span>)");
};

Keyword.prototype.limit = function () {
    this.keywords.hide().each(function () {

        if ($("[data-keywords~=" + $(this).find("input").val() + "]").size()) {
            $(this).show().find("input").attr("checked", "checked");
        }
    });
};

Keyword.prototype.filter = function (keyword, show) {

    if (show) {
        $("#search-results article[data-keywords~=" + keyword + "]").show();
    } else {
        $("#search-results article[data-keywords~=" + keyword + "]").hide();
    }
};

Keyword.prototype.update_counts = function () {
    this.keywords.each(function () {
        var count = $("#search-results article[data-keywords~=" + $(this).find("input").val() + "]").size();
        $(this).find("span.count").html(count);
    });
};


var Category = function () {
    this.categories = $("#filter-categories label");
    this.categories.append(" (<span class=\"count\">0</span>)");
};

Category.prototype.limit = function () {
    this.categories.hide().each(function () {
        if ($("article[data-category=" + $(this).find("input").val() + "]").size()) {
            $(this).show().find("input").attr("checked", "checked");
        }
    });
};

Category.prototype.filter = function (category, show) {
    // we do this a lot
    if (show) {
        $("#search-results article[data-category=" + category + "]").show();
    } else {
        $("#search-results article[data-category=" + category + "]").hide();
    }
};

Category.prototype.update_counts = function () {
    // this is the same method as the Keyword update_counts???
    this.categories.each(function () {
        var count = $("#search-results article[data-category=" + $(this).find("input").val() + "]").size();
        $(this).find("span.count").html(count);
    });
};


var filterResults = function (type, show) {

    if (show) {
        $("#search-results article." + type).show();
    } else {
        $("#search-results article." + type).hide();
    }
};

var filterDates = function (dates) {
    var d1 = $(dates[0]).val().replace(/-/g, ""),
        d2 = $(dates[1]).val().replace(/-/g, "");

    $("#search-results article").each(function () {
        if (d2 >= $(this).data("modified-date") && $(this).data("modified-date") >= d1) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
};

/* 
   Main search function
*/
var doSearch = function (options) {
    var query      = options.query,
        categories = options.categories,
        keywords   = options.keywords;

    $("#search-results").html("<p>Searching...</p>");
    $(".search_query").html(query);

    $.getJSON('/search/api', {"q": query, "limit": "none"}, function (data) {
        $("#search-results").html("");

        // if there are results
        if (data.results.length) {
            var d1 = data.results[0].last_modified;

            $.each(data.results, function (index, item) {
                var context = {
                    "display_type": item._display_type,
                    "date": item.date,
                    "url": item.detail,
                    "title": item.title,
                    "keywords": item.keywords,
                    "owner": item.owner,
                    "owner_url": item.owner_detail,
                    "popular": index === 0 ? item.rating : 23, // item.rating when popularity data is established
                    "last_modified": item.last_modified.split(".")[0].replace(/[\-T:]/g, ""),
                    "last_modified_date": item.last_modified.split("T")[0].replace(/-/g, "")
                };

                if (item.category !== undefined) {
                    // use dot notation instead of array look up syntax
                    context.category = item.category[0];
                    context.category_slug = item.category[0].toLowerCase().replace(/ /g, "-");
                }

                $("#search-results").append(srt.render(context));
                if (d1 > item.last_modified) {
                    d1 = item.last_modified;
                }
            });
            // end of each loop

            $("#id_data_begins").val(d1.split("T")[0]);
            $(".info-bar").show().find(".count").html($("#search-results article").size());
            $("#filter-classes :checkbox").attr("checked", "checked");

            $("#filter-classes span.count").each(function () {
                $(this).html(
                    $("#search-results article." + $(this).parents("label").data("class")).size()
                );
            });
        }

        if ($("#search-results article").size()) {
            $(".info-bar select").show();
        } else {
            $(".info-bar select").hide();
            $("#search-results").html("<p>No results</p>");
        }

        keywords.update_counts();
        categories.limit();
        categories.update_counts();
    });
    // end of response to ajax call
};


$(function () {
    // show these class names be plural?
    var related_searches = new RelatedSearch(),
        keywords = new Keyword(),
        categories = new Category();

    // make the doSearch function global while retaining access to the
    // keywords and categories vars
    window.globalDoSearch = function (query) {
        doSearch({
            query: query,
            keywords: keywords,
            categories: categories
        });
    };


    $("form.search-box").bind("submit", function (e) {
        e.preventDefault();
        window.globalDoSearch($(this).find("input[name=q]").val());
    });

    $("#filter-classes label.checkbox").each(function () {
        $(this).find("input[type=checkbox]").change(function () {
            // should this be a == or a === ?
            filterResults($(this).parents("label").data("class"), $(this).attr("checked") === "checked");
        });
    });

    $("#id_sorting").change(function () {
        var sortby = $(this).val();
        $('#search-results > article').tsort({order: 'desc', data: sortby});
    });

    $(".expand-content").click(function (event) {
        event.preventDefault();
    });

    $(".datepicker").datepicker().on('changeDate', function (ev) {
        filterDates($(".datepicker"));
    });

    $("#filter-categories input[type=checkbox]").change(function () {
        categories.filter($(this).val(), $(this).attr("checked") === "checked");
    });

    $("#filter-keywords input[type=checkbox]").change(function () {
        keywords.filter($(this).val(), $(this).attr("checked") === "checked");
    });

    // view
    $(".view .thumb").click(function (event) {
        $(this).addClass('current');
        $('.view .list').removeClass('current');
        $('#search-results').addClass("row");
        $('#search-results article').wrap('<div class="span4" />'); /// fix this use of jquery
        $('#search-results article img').attr('width', '100%');
        event.preventDefault();
    });

    $(".view .list").click(function (event) {
        $(this).addClass('current');
        $('.view .thumb').removeClass('current');
        $('#search-results').removeClass('row');
        $('#search-results article').unwrap('<div class="span4" />');
        $('#search-results article img').attr('width', '25%');
        event.preventDefault();
    });

});
