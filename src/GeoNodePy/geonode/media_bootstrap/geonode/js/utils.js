var perms_submit = function() {
    var form = $(this);
    var action = form.attr("action");

    permissions = permissionsString(form.serializeObject());
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
    postdata.permissions = permissionsString(form.serializeObject());
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

function permissionsString(data) {
  var anonymousPermissions, authenticatedPermissions;

  var levels = {
    'admin': 'layer_admin',
    'readwrite': 'layer_readwrite',
    'readonly': 'layer_readonly',
    'none': '_none'
  };

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
    if (data["editusers"] instanceof Array) {
      $.each(data["editusers"], function(index, value) {
        perUserPermissions.push([value, levels["readwrite"]]);
      });
    } else {
      perUserPermissions.push([data["editusers"], levels["readwrite"]]);
    };
    
  }
  if (data["editusers"]) {

    if (data["editusers"] instanceof Array) {
      $.each(data["manageusers"], function(index, value) {
        perUserPermissions.push([value, levels["admin"]]);
      });
    } else {
      perUserPermissions.push([data["manageusers"], levels["admin"]]);
    };

  };


  return {
    anonymous: anonymousPermissions,
    authenticated: authenticatedPermissions,
    users: perUserPermissions
  };
};
