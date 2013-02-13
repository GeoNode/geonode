$(function(){
    $('.trigger-query').click(
        function(){
            // manage the activation deactivation of the filter on click
            $(this).hasClass('active') ? $(this).removeClass('active') 
                : $(this).addClass('active');

            // logic to make sure that whne clicking on the layer filter it also 
            //activats/deactivated vector and raster
            if ($(this).attr('data-class') === 'layer'){
                if($(this).hasClass('active')){
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
            if ($(this).parents('ul').attr('id') === 'categories' && $(this).attr('data-class') === 'all'){
                if ($(this).hasClass('active')){
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
                keywords: []
            }
            
            // traverse the active filters to build the query parameters
            $('.tabs-left > ul').each(function(){
                var id = $(this).attr('id');
                $(this).find('.active').each(function(){
                    params[id].push($(this).attr('data-class'));
                });
            });
            
            if(params['categories'][0] === 'all'){
                params['categories'].shift();
            }

            $.ajax({
                type: 'POST',
                url: '/search/html',
                data: {
                    type: params['types'].join(','),
                    category: params['categories'].join(',')
                }, 
                success: function(data){
                    $('#search-content').html(data);
                    paginate();
                    rateMore();
                }
            });
        }
    );
});