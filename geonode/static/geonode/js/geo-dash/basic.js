function deepClone(item) {
    if (!item) { return item; } // null, undefined values check

    var types = [Number, String, Boolean],
        result;

    // normalizing primitives if someone did new String('aaa'), or new Number('444');
    types.forEach(function (type) {
        if (item instanceof type) {
            result = type(item);
        }
    });

    if (typeof result == "undefined") {
        if (Object.prototype.toString.call(item) === "[object Array]") {
            result = [];
            item.forEach(function (child, index, array) {
                result[index] = deepClone(child);
            });
        } else if (typeof item == "object") {
            // testing that this is DOM
            if (item.nodeType && typeof item.cloneNode == "function") {
                var result = item.cloneNode(true);
            } else if (!item.prototype) { // check that this is a literal
                if (item instanceof Date) {
                    result = new Date(item);
                } else {
                    // it is an object literal
                    result = {};
                    for (var i in item) {
                        result[i] = deepClone(item[i]);
                    }
                }
            } else {
                // depending what you would like here,
                // just keep the reference, or create new object
                if (false && item.constructor) {
                    // would not advice to do that, reason? Read below
                    result = new item.constructor();
                } else {
                    result = item;
                }
            }
        } else {
            result = item;
        }
    }

    return result;
}

/**
 * Slide right instantiation and action.
 */
var slideRight = new Menu({
    wrapper: '#gd-wrapper',
    type: 'slide-right',
    menuOpenerClass: '.c-button',
    maskId: '#c-mask'
});

var slideRightBtn = document.querySelector('#c-button--slide-right');

if(slideRightBtn != null){
    slideRightBtn.addEventListener('click', function(e) {
        e.preventDefault;
        slideRight.open();
    });
}

$(window).scroll(function() {
    if ($(this).scrollTop() > 50){
        //$('#gd-header').addClass("sticky");
    }
    else{
        //$('#gd-header').removeClass("sticky");
    }
});

function anyonePermissionDisable(){
    if($('#perms_view_anyone').length>0){
        //$('#perms_view_anyone').attr('disabled', 'disabled');
        $('input#perms_view_anyone').filter(':checkbox').prop('checked',false);

        //$('#perms_download_resourcebase_anyone').attr('disabled', 'disabled');
        $('input#perms_download_resourcebase_anyone').filter(':checkbox').prop('checked',false);
    }
}
function anyonePermissionEnabel(){
    if($('#perms_view_anyone').length>0){
        $('#perms_view_anyone').removeAttr('disabled');
        $('#perms_download_resourcebase_anyone').removeAttr('disabled', 'disabled');
    }
}
function approvePermission(){
    if($('#perms_view_anyone').length>0){
        $('#perms_view_anyone').removeAttr('disabled');
        $('input#perms_view_anyone').filter(':checkbox').prop('checked',true);
        $('#perms_download_resourcebase_anyone').removeAttr('disabled', 'disabled');
        $('input#perms_download_resourcebase_anyone').filter(':checkbox').prop('checked',true);
    }
}
$(document).ready(function() {
    if( $(".modal").length > 0){
        $('.modal').on('shown.bs.modal', function () {
            if($('.gxp-icon-googleearth').length > 0){
                var googleEarthActive = $('.gxp-icon-googleearth').closest('table.x-btn').hasClass('x-btn-pressed');
                if(googleEarthActive){
                    $(this).addClass('google-earth');
                } else {
                    $(this).removeClass('google-earth');
                }
            } else {
                $(this).removeClass('google-earth');
            }
        });
    }
    if( $(".animation_conuter").length){
        $('.animation_conuter').each(function () {
            $(this).prop('Counter',0).animate({
                Counter: $(this).text()
            }, {
                duration: 2000,
                easing: 'swing',
                step: function (now) {
                    $(this).text(Math.ceil(now));
                }
            });
        });
    }
/*    if( $(".animation_conuter_maps").length){
        var JS_STATIC_URL = '../api/maps';
        $.ajax({
        url: JS_STATIC_URL,
        type: 'GET',
        data: {},
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        context: document.body,
        success: function(jsondata){
            //console.log(JSON.stringify(jsondata));
            var data = eval(jsondata.objects);
            var t_count = data.length;
            //alert(t_count);
            $("#total_maps_home").text(t_count);
            //$("#total_layers_home");
            $('.animation_conuter_maps').each(function () {
            $(this).prop('Counter',0).animate({
                Counter: $(this).text()
            }, {
                duration: 2000,
                easing: 'swing',
                step: function (now) {
                    $(this).text(Math.ceil(now));
                }
            });
        });
        }});
    }
*/
    if( $("body.layer-detail-page #gd-wrapper").length){
        $('.modal').on('shown.bs.modal', function () {
            $("body.layer-detail-page #gd-wrapper").css("position","absolute");
        });
        $('.modal').on('hide.bs.modal', function () {
            $("body.layer-detail-page #gd-wrapper").css("position","fixed");
        });
    }
    if( $("body.map-detail-page #gd-wrapper").length){
        $('.modal').on('shown.bs.modal', function () {
            $("body.map-detail-page #gd-wrapper").css("position","absolute");
        });
        $('.modal').on('hide.bs.modal', function () {
            $("body.map-detail-page #gd-wrapper").css("position","fixed");
        });
    }

    $("#advanced-search-control, .advanced-search-control").click(function() {
        $("#gd-advanced-search").slideToggle("slow");
    });

    // cart section
    $(".selectfixed").on({
        "shown.bs.dropdown": function() {
            this.closable = false;
        },
        "click":             function() {
            this.closable = true;
        },
        "hide.bs.dropdown":  function() {
            return this.closable;
        }
    });
    $("#show-notification").click(function() {
        $("#show-notification-msg").slideToggle("slow");
        return false;
    });
    $("body").click(function() {
        $("#show-notification-msg").slideUp("slow");
    });

});

    $(document).ready(function() {
        $('.notifications').click(function() {
            $("#show-notification").load(location.href+" #show-notification>*","");
        });
    });
//    $(document).ready(function() {
//        $('.unreadfalse').click(function() {
//            $(".unreadfalse").load(location.href+" .unreadfalse>*","");
//        });
//    });
    $(document).ready(function() {
        $('.gd-featurd-maps-container-dash').click(function() {
            $(".dash-load").load(location.href+" .dash-load>*","");
        });
    });
    $(document).ready(function() {
        $('#toolbar_remove').click(function() {
            $("#toolbar_hide").remove();;
        });
    });