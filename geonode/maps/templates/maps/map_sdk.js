{% include 'geonode/ext_header.html' %}
{% include 'geonode/sdk_header.html' %}
<style type="text/css">
.map-title-header {
    margin-right: 10px;
}
</style>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/GeoNode-GeoExplorer.js"></script>
<script type="text/javascript">
var app;
Ext.onReady(function() {
{% autoescape off %}
    var config = Ext.apply({
        authStatus: {% if user.is_authenticated %} 200{% else %} 401{% endif %},
        proxy: '{{ PROXY_URL }}',
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
        portalItems: [{
            xtype: "container",
            layout: "fit",
            height: 81,
            region: "north"
        }],
        localGeoServerBaseUrl: "{{ GEOSERVER_BASE_URL }}",
        localCSWBaseUrl: "{{ CATALOGUE_BASE_URL }}",
        csrfToken: "{{ csrf_token }}",
        tools: [{ptype: "gxp_getfeedfeatureinfo"}],
    }, {{ config }});


    app = new MyApp.Viewer(config);
{% endautoescape %}
});
</script>
