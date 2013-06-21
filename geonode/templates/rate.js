{% load staticfiles %}
<script type="text/javascript">
  requirejs.config({
    paths:{
      'jquery.raty': '/static/lib/js/jquery.raty.min'
    } 
  });
  require(['jquery.raty'], function(raty){
    
    function rateMore() {
      $('.overall_rating').each(function() {
        var rating = $(this).parents(".avg_rating").data('rating');
        star(this, rating);
      });
      $(".loadmore").on("load.loadmore", function(e, o) {          
        o.find(".overall_rating").each(function() {
          var rating = $(this).parents(".avg_rating").data('rating');
          star(this, rating);
        });
      });
    }
    function star(elem, rating) {
      $(elem).raty({
        half: true,
        readOnly: true,
        score: rating,
        path: "{% static "agon_ratings/img/" %}"
      });        
    }
    $(rateMore());
    $(document).on('rateMore',rateMore)
  });
</script>
