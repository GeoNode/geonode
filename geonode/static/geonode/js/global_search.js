requirejs.config({
    baseUrl: '/static/libs/js',
    paths: {
        'app': '../../geonode/js'
    }
});

define(['jquery','waypoints'],function($){
    
    function build_query(){
        /*
        * Builds the "data" parameter used in the ajax query. Collects all the parameters from the page
        */
        var params = {
            types: [],
            categories: [],
            keywords: [],
            date_start: [],
            date_end: [],
            sort: []
        }
        
        // traverse the active filters to build the query parameters
        $('.filter > ul').each(function(){
            var id = $(this).attr('id');
            $(this).find('.active').each(function(){
                params[id].push($(this).attr('data-class'));
            });
        });
        
        if(params['date_start'][0] === 'yyyy-mm-dd'){
            params['date_start'] = ['']
        }
        if(params['date_end'][0] === 'yyyy-mm-dd'){
            params['date_end'] = ['']
        }
        //from the client we don't use the all key for the categories
        if(params['categories'][0] === 'all'){
            params['categories'].shift();
        }

        var data = {
            'type': params['types'].join(','),
            'category': params['categories'].join(','),
            'kw': params['keywords'].join(','),
            'start_date': params['date_start'][0],
            'end_date': params['date_end'][0],
            'sort': params['sort'][0]
        }
        if (typeof default_type != 'undefined'){
            data['type'] = default_type;
        }
        return data
    }

    function query(){
        /*
        * Sends the query used for search
        */
        var data = build_query()
        $.ajax({
            type: 'POST',
            url: '/search/html',
            data: data, 
            success: function(data){
                $('#search-content').html(data);
                //call the pagination
                paginate();
                //call the rating update
                $(document).trigger('rateMore');
            }
        });
    }

    function manage_element(element){
        /*
        * Manage the classes of the filters on the page
        */

        // logic to make sure that whne clicking on the layer filter it also 
        //activate/deactivated vector and raster
        if ($(element).attr('data-class') === 'layer'){
            if($(element).hasClass('active')){
                $('a[data-class="raster"]').addClass('active');
                $('a[data-class="vector"]').addClass('active');
            }
            else{
                $('a[data-class="raster"]').removeClass('active');
                $('a[data-class="vector"]').removeClass('active');
            }
        }

        // logic to make sure that clicking on the all categories it also
        // activate/deactivate all other categories
        if ($(element).parents('ul').attr('id') === 'categories' && $(element).attr('data-class') === 'all'){
            if ($(element).hasClass('active')){
                $('#categories').find('a').each(function(){
                    $(this).removeClass('active');
                });
                $(element).addClass('active');
            } 
        }
        else if ($(element).parents('ul').attr('id') === 'categories'){
            $('a[data-class="all"]').removeClass('active');
        }
    }

    var loading = "<div class='loading'><p>Loading more items&hellip;</p></div>";
    function fetchMore(a) {
        /*
        * Fetch more results respecting the current query
        */
        $(a).before($(loading));
        $.ajax({
            type: 'POST',
            url: $(a).attr('href'),
            data: build_query(),
            context: $(a).parents(".paginate"),
            success: function(data, status, jqxhr) {
                var $data = $(data).find(".paginate");
                var articles = $data.find('.paginate-contents article');
                var more = $data.find("a.next").attr("href");
                $(this).find(".paginate-contents").append(articles).trigger("paginate.loaded", [articles]);
                $(this).find(".loading").detach();
                if (more) {
                    $(this).find('.more').attr("href", more);
                    if ($(this).hasClass("paginate-auto")) $(this).find(".pagination").waypoint(opts);
                } else $(this).find('.more').remove();
                $(document).trigger('rateMore');
            }
        });
    }
        
    function paginate() {
        /*
        * Main pagination function
        */
        $(".paginate").each(function() {
            var p$ = $(this);
            var auto = p$.hasClass("paginate-auto") ? true : false,
            hasMore = parseInt(p$.find(".pagination .current.page").html(),10) < parseInt(p$.find(".pagination .page_total").html(),10),
            $pages = p$.find(".pagination");
            opts = {
                offset: '100%'
            };

            if (hasMore && !$("html.ie8").size()) {
                $pages.children().hide();
                if (auto) {
                    $pages.waypoint(function(event, direction) {
                        $pages.waypoint('remove');
                        fetchMore($(this).find("a.more").get(0));
                    }, opts);
                } else {
                    $pages.prepend($("<a></a>", {
                        href: $pages.find("a.more").attr("href"),
                        html: "<i class=\"icon-chevron-down\"></i> Show more",
                        "class": "more"
                        }
                    ).click(function(e) {
                        e.preventDefault();
                        fetchMore(this);
                    }));
                }
            }
        });
    }
    
    paginate();

    // add some listeners
    $('.trigger-query').click(
        function(){
            // manage the activation deactivation of the filter on click
            $(this).hasClass('active') ? $(this).removeClass('active') : $(this).addClass('active');
            manage_element($(this));
            query();
        }
    );
    $('.datepicker').change(
        function(){
            $(this).addClass('active');
            $(this).attr('data-class', $(this).val());
            manage_element(this);
            query();
        } 
    );
    $('.date-query').click(
        function(){
            // manage the activation deactivation of the filter on click
            $('.date-query').removeClass('active');
            $('.date-query').removeClass('selected');
            $(this).addClass('active');
            $(this).addClass('selected');
            manage_element($(this));
            query();
        }
    );
});