/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/libs/js'
});

define(['jquery'],function($){
    return {
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
        }
    }
});