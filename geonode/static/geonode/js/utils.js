$(function() {
    // Topbar active tab support
    $(".main-nav li").removeClass("current");

//    $('[rel=tooltip]').tooltip({placement:"left"});
    
    var class_list = $("body").attr("class").split(/\s+/);
    $.each(class_list, function(index, item) {
        var selector = ".main-nav li#nav_" + item;
        $(selector).addClass("current");
    });
    $('#login-link').click(function(e) {
        e.preventDefault();
        var href = $(this).attr('href');
        if (href[0] == '/') {
            $.post(href,{},function(d,s,x) {
                window.location.reload();
            })
        } else {
            $(href).toggle();
        }
    });

    $("#login-form-pop button").click(function(e) {
        var form = $("#login-form-pop form");
        e.preventDefault();
        if (!navigator.cookieEnabled) {
            alert('GeoNode requires cookies to be enabled.');
            return;
        }
        $.post(form.attr('action'),form.serialize(),function(data,status,xhr) {
            $('.loginmsg').hide();
            if (status == 'success') {
                window.location.reload();
            } else {
                alert(data);
            }
            $("#login-form-pop").toggle();
        }).error(function(data,status,xhr) {
            if (status == 'error') {
                $('.loginmsg').text('Invalid login').slideDown();
            }
        });
    });
});

//define(['jquery'], function($) {

$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
      if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
          var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
      return (url == origin || url.slice(0, origin.length + 1) == origin + '/') || (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

var batch_delete = function() {
  var form = $(this);
  var action = form.attr("action");

  var postdata = { layers: [], maps: [] };
  var selected = $(".asset-selector:checked");

  $.each(selected, function(index, value) {
      var el = $(value);
      if (el.data("type") === "map") {
          postdata.maps.push(el.data("id"));
      } else if (el.data("type") === "layer") {
          postdata.layers.push(el.data("id"));
      }
  });

  if (postdata.layers.length == 0) {
      delete postdata.layers;
  };

  if (postdata.maps.length == 0) {
      delete postdata.maps;
  };

};

$.fn.serializeObject = function() {
    var o = {};
    var a = this.serializeArray();

    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};


// what is going on here?, It looks like someone is trying to include
// all of these global functions as static methods of the pub object.
// This section could be update to use require.js

var pub = {

    batch_delete: function() {
      var form = $(this);
      var action = form.attr("action");

      var postdata = {
        layers: [],
        maps: []
      };
      var selected = $(".asset-selector:checked");

      $.each(selected, function(index, value) {
          var el = $(value);
          if (el.data("type") === "map") {
              postdata.maps.push(el.data("id"));
          } else if (el.data("type") === "layer") {
              postdata.layers.push(el.data("id"));
          }
      });

      if (!postdata.layers.length) {
        delete postdata.layers;
      }
      if (!postdata.maps.length) {
        delete postdata.maps;
      }

      $.ajax({
        type: "POST",
        url: action,
        data: JSON.stringify(postdata),
        success: function(data) {
          $("#delete_form").modal("hide");
        }
      });
      return false;
    },

    batch_perms_submit: function() {
        var form = $(this);
        var action = form.attr("action");

        var postdata = {
            layers: [],
            maps: [],
            permissions: {}
        };

        var selected = $(".asset-selector:checked");

        $.each(selected, function(index, value) {
            var el = $(value);
            if (el.data("type") === "map") {
                postdata.maps.push(el.data("id"));
            } else if (el.data("type") === "layer") {
                postdata.layers.push(el.data("id"));
            }
        });

        if (!postdata.layers.length) {
            delete postdata.layers;
        }

        if (!postdata.maps.length) {
            delete postdata.maps;
        }

        postdata.permissions = permissionsString(form, "bulk");
        $.ajax({
            type: "POST",
            url: action,
            data: JSON.stringify(postdata),
            success: function(data) {
                $("#modal_perms").modal("hide");
            }
        });
        return false;
    },
};
