{% include 'geonode/ext_header.html' %}
{% include 'geonode/geo_header.html' %}
<style type="text/css">
#aboutbutton {
    display: none;
}
#paneltbar {
    margin-top: 81px;
}
button.logout {
    display: none;
}
button.login {
    display:none;
}
.map-title-header {
    margin-right: 10px;
}
</style>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/thumbnail/map_thumbnail.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/GeoNode-mixin.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/GeoNode-GeoExplorer.js"></script>
<script type="text/javascript">
var app;
Ext.onReady(function() {
{% autoescape off %}
    GeoExt.Lang.set("{{ LANGUAGE_CODE }}");
    var config = Ext.apply({
        authStatus: {% if user.is_authenticated %} 200{% else %} 401{% endif %},
        {% if PROXY_URL %}
        proxy: '{{ PROXY_URL }}',
        {% endif %}
        {% if PRINT_NG_ENABLED %}
        listeners: {
            'save': function(obj_id) {
                createMapThumbnail(obj_id);
            }
        },
        {% endif %}
        {% if MAPFISH_PRINT_ENABLED %}
        printService: "{{GEOSERVER_BASE_URL}}pdf/",
        {% else %}
        printService: "",
        {% endif %} 
        /* The URL to a REST map configuration service.  This service 
         * provides listing and, with an authenticated user, saving of 
         * maps on the server for sharing and editing.
         */
        rest: "{% url "maps_browse" %}",
        ajaxLoginUrl: "{% url "account_ajax_login" %}",
        homeUrl: "{% url "home" %}",
        localGeoServerBaseUrl: "{{ GEOSERVER_BASE_URL }}",
        localCSWBaseUrl: "{{ CATALOGUE_BASE_URL }}",
        csrfToken: "{{ csrf_token }}",
        tools: [{ptype: "gxp_getfeedfeatureinfo"}],
    }, {{ config }});


    app = new GeoNode.Composer(config);
    app.mapPanel.map.addControl(
        new OpenLayers.Control.MousePosition(
            { numDigits: 2,
              displayProjection: new OpenLayers.Projection("EPSG:4326")}
        )
    );

{% endautoescape %}
});
</script>
