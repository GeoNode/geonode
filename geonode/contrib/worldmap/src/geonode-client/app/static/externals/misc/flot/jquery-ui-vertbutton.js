(function( $ ){
//plugin buttonset vertical
$.fn.buttonsetv = function() {
  $(':radio, :checkbox', this).wrap('<div style="margin: 1px"/>');
  $(this).buttonset();
  $('label:first', this).removeClass('ui-corner-left').addClass('ui-corner-top');
  $('label:last', this).removeClass('ui-corner-right').addClass('ui-corner-bottom');
  mw = 0; // max witdh
  $('label', this).each(function(index){
     w = $(this).width();
     if (w > mw) mw = w; 
  })
  $('label', this).each(function(index){
    $(this).width(mw);
  })
};
})( jQuery );
