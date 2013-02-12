$(function(){
    $('.trigger-query').click(
        function(){
            $(this).hasClass('active') ? $(this).removeClass('active') 
                : $(this).addClass('active');
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
            
            var params = {
                types: [],
                categories: [],
                keywords: []
            }
            
            $('.tabs-left > ul').each(function(){
                var id = $(this).attr('id');
                $(this).find('.active').each(function(){
                    params[id].push($(this).attr('data-class'));
                });
            });
            
            $.ajax({
                type: 'POST',
                url: '/search/html',
                data: {
                    type: params['types'].join(',')
                }, 
                success: function(data){
                    $('#search-content').html(data);
                    paginate();
                }
            });
        }
    );
});