/**
 * Created by jahangir on 10/22/17.
 */

//$(window).load(function(){

    // "ext-gen61" pan button ID
    // "ext-gen64" click button ID
    // "ext-gen75" zoom in button ID
    // "ext-gen77" zoom out button ID

    getLocation();

    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(setPosition);
        }

    }

    function setPosition(position) {
        var user_location = {
            "latitude": position.coords.latitude,
            "longitude": position.coords.longitude
        };

        if (typeof(Storage) !== "undefined") {
            localStorage.setItem("user_location", JSON.stringify(user_location));
        }
    }

    function user_activity_submit(data, url){

        // using jQuery
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        var csrftoken = getCookie('csrftoken');
        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });

        $.ajax({
            url: url,
            method: 'POST',
            data: data,
            dataType: 'json',
            success: function(data){
                console.log(data);

            }
        });

    }

    function visitor(){

        if(typeof(Storage) !== "undefined") {
            if (sessionStorage.clickcount) {
                sessionStorage.clickcount = Number(sessionStorage.clickcount)+1;
            } else {
                sessionStorage.clickcount = 1;
            }

            if(sessionStorage.clickcount <= 2){

                var user_location = JSON.parse(localStorage.getItem("user_location"));

                // console.log(user_location.latitude);
                // console.log(user_location.longitude);

                var url = '/analytics/api/visitor/create/';

                var data = {
                    'user': user_info == undefined ? '' : user_info,
                    'page_name': '',
                    'latitude': user_location.latitude.toString(),
                    'longitude': user_location.longitude.toString(),
                    'agent': '',
                    'ip': ''
                };

                user_activity_submit(data, url);
            }

        }
    }

    // pan activity
    $("#ext-gen61").on('click', function(e){

        var user_location = JSON.parse(localStorage.getItem("user_location"));

        var url = '/analytics/api/user/activity/create/';

        var data = {
            'user': user_info,
            'layer': layer_info,
            'map': map_info,
            'activity_type': 'pan',
            'latitude': user_location.latitude.toString(),
            'longitude': user_location.longitude.toString(),
            'agent': '',
            'ip': '',
            'point': ''
        };

        user_activity_submit(data, url);

    });

    // click activity
    $("#ext-gen64").on('click', function(e){

        var user_location = JSON.parse(localStorage.getItem("user_location"));

        var url = '/analytics/api/user/activity/create/';

        var data = {
            'user': user_info,
            'layer': layer_info,
            'map': map_info,
            'activity_type': 'click',
            'latitude': user_location.latitude.toString(),
            'longitude': user_location.longitude.toString(),
            'agent': '',
            'ip': '',
            'point': ''
        };

        user_activity_submit(data, url);

    });

    // zoom in activity
    $("#ext-gen75").on('click', function(e){

        var user_location = JSON.parse(localStorage.getItem("user_location"));

        var url = '/analytics/api/user/activity/create/';

        var data = {
            'user': user_info,
            'layer': layer_info,
            'map': map_info,
            'activity_type': 'zoom',
            'latitude': user_location.latitude.toString(),
            'longitude': user_location.longitude.toString(),
            'agent': '',
            'ip': '',
            'point': ''
        };

        user_activity_submit(data, url);
    });

    // zoom out activity
    $("#ext-gen77").on('click', function(e){

        var user_location = JSON.parse(localStorage.getItem("user_location"));

        var url = '/analytics/api/user/activity/create/';

        var data = {
            'user': user_info,
            'layer': layer_info,
            'map': map_info,
            'activity_type': 'zoom',
            'latitude': user_location.latitude.toString(),
            'longitude': user_location.longitude.toString(),
            'agent': '',
            'ip': '',
            'point': ''
        };

        user_activity_submit(data, url);
    });

    // visitor activity
    visitor();

    // Layer Load


//});
