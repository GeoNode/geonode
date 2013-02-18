$(function(){
    function query(element){

            // logic to make sure that whne clicking on the layer filter it also 
            //activats/deactivated vector and raster
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
                        $(this).addClass('active');
                    })
                } else {
                    $('#categories').find('a').each(function(){
                        $(this).removeClass('active');
                    })
                }
            }
            
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
            $.ajax({
                type: 'POST',
                url: '/search/html',
                data: {
                    'type': params['types'].join(','),
                    'category': params['categories'].join(','),
                    'kw': params['keywords'].join(','),
                    'start_date': params['date_start'][0],
                    'end_date': params['date_end'][0],
                    'sort': params['sort'][0]
                }, 
                success: function(data){
                    $('#search-content').html(data);
                    //call the pagination
                    paginate();
                    //call the rating update
                    rateMore();
                }
            });
        }
    $('.trigger-query').click(
        function(){
            // manage the activation deactivation of the filter on click
            $(this).hasClass('active') ? $(this).removeClass('active') : $(this).addClass('active');
            query($(this));
        }
    );
    $('.datepicker').change(
        function(){
            $(this).addClass('active');
            $(this).attr('data-class', $(this).val());
            query(this);
        } 
    );
    $('.date-query').click(
        function(){
            // manage the activation deactivation of the filter on click
            $('.date-query').removeClass('active');
            $('.date-query').removeClass('selected');
            $(this).addClass('active');
            $(this).addClass('selected');
            query($(this));
        }
    );
});