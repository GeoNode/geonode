jQuery(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
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
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
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

var map_perms_submit = function() {
    var form = $(this);
    var action = form.attr("action");

    permissions = permissionsString(form, "maps");
    $.ajax(
      {
        type: "POST",
        url: action,
        data: JSON.stringify(permissions),
        success: function(data) {
          $("#modal_perms").modal("hide");
        }
      }
    );
    return false;
};

var layer_perms_submit = function() {
    var form = $(this);
    var action = form.attr("action");

    permissions = permissionsString(form, "layer");
    $.ajax(
      {
        type: "POST",
        url: action,
        data: JSON.stringify(permissions),
        success: function(data) {
          $("#modal_perms").modal("hide");
        }
      }
    );
    return false;
};

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

  $.ajax(
    {
      type: "POST",
      url: action,
      data: JSON.stringify(postdata),
      success: function(data) {
        $("#delete_form").modal("hide");
      }
    }
  );
  return false;
};

var batch_perms_submit = function() {
    var form = $(this);
    var action = form.attr("action");

    var postdata = { layers: [], maps: [], permissions: {} };
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

    postdata.permissions = permissionsString(form, "bulk");
    $.ajax(
      {
        type: "POST",
        url: action,
        data: JSON.stringify(postdata),
        success: function(data) {
          $("#modal_perms").modal("hide");
        }
      }
    );
    return false;
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

function permissionsString(form, type) {
  var anonymousPermissions, authenticatedPermissions;

  var data = form.serializeObject();

  if (type == "maps") {
    var levels = {
      'readonly': 'map_readonly',
      'readwrite': 'map_readwrite',
      'admin': 'map_admin',
      'none': '_none'
    };
  } else {
    var levels = {
      'admin': 'layer_admin',
      'readwrite': 'layer_readwrite',
      'readonly': 'layer_readonly',
      'none': '_none'
    };
  }

  if (data["viewmode"] === "ANYONE") {
    anonymousPermissions = levels['readonly'];
  } else {
    anonymousPermissions = levels['none'];
  }

  if (data["editmode"] === "REGISTERED") {
    authenticatedPermissions = levels['readwrite'];
  } else if (data["viewmode"] === 'REGISTERED') {
    authenticatedPermissions = levels['readonly'];
  } else {
    authenticatedPermissions = levels['none'];
  }

  var perUserPermissions = [];
  if (data["editmode"] === "LIST") {
    var editusers = form.find("input[name=editusers]").select2("val");
    if (editusers instanceof Array) {
      $.each(editusers, function(index, value) {
        perUserPermissions.push([value, levels["readwrite"]]);
      });
    } else {
      perUserPermissions.push([editusers, levels["readwrite"]]);
    };
  }
  var manageusers = form.find("input[name=manageusers]").select2("val");
  if (manageusers) {
    if (manageusers instanceof Array) {
      $.each(manageusers, function(index, value) {
        perUserPermissions.push([value, levels["admin"]]);
      });
    } else {
      perUserPermissions.push([manageusers, levels["admin"]]);
    };
  };


  return {
    anonymous: anonymousPermissions,
    authenticated: authenticatedPermissions,
    users: perUserPermissions
  };
};
