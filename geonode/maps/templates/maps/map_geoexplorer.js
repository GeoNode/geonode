{% include 'geonode/ext_header.html' %}
{% include 'geonode/geo_header.html' %}
<link href="{{ STATIC_URL}}geonode/css/geoexplorer/map_geoexplorer.css" rel="stylesheet"/>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/GeoNode-mixin.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/Geonode-CatalogueApiSearch.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/GeoNode-GeoExplorer.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/utils/thumbnail.js"></script>
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
        listeners: {
            "ready": function() {
                app.mapPanel.map.getMaxExtent = function() {
                    return new OpenLayers.Bounds(-80150033.36/2,-80150033.36/2,80150033.36/2,80150033.36/2);
                }
                app.mapPanel.map.getMaxResolution = function() {
                    return 626172.135625/2;
                }
                l = app.selectedLayer.getLayer();
                l.addOptions({wrapDateLine:true, displayOutsideMaxExtent: true});
                l.addOptions({maxExtent:app.mapPanel.map.getMaxExtent(), restrictedExtent:app.mapPanel.map.getMaxExtent()});
                for (var l in app.mapPanel.map.layers) {
                    l = app.selectedLayer.getLayer();
                    l.addOptions({wrapDateLine:true, displayOutsideMaxExtent: true});
                    l.addOptions({maxExtent:app.mapPanel.map.getMaxExtent(), restrictedExtent:app.mapPanel.map.getMaxExtent()});
                }

                var map = app.mapPanel.map;
                var layer = app.map.layers.slice(-1)[0];

                // FIXME(Ariel): Zoom to extent until #1795 is fixed.
                //map.zoomToExtent(layer.maxExtent, false)

                var bbox = layer.bbox;
                if (bbox != undefined)
                {
                   if (!Array.isArray(bbox) && Object.keys(layer.srs) in bbox) {
                    bbox = bbox[Object.keys(layer.srs)].bbox;
                   }

                   var extent = OpenLayers.Bounds.fromArray(bbox);
                   var zoomToData = function()
                   {
                       map.zoomToExtent(extent, false);
                       app.mapPanel.center = map.center;
                       app.mapPanel.zoom = map.zoom;
                       map.events.unregister('changebaselayer', null, zoomToData);
                   };
                   map.events.register('changebaselayer',null,zoomToData);
                   if(map.baseLayer){
                    map.zoomToExtent(extent, false);
                   }
                }
            },
           'save': function(obj_id) {
               createMapThumbnail(obj_id);
           }
       }
    }, {{ config }});

    app = new GeoNode.Composer(config);
{% endautoescape %}
});
</script>
