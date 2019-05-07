{% include "geoext/ext_header.html" %}
{% include "geoext/app_header.html" %}
{% include "geoext/geo_header.html" %}
{% load static from staticfiles %}

<link href="{% static "geonode/css/geoexplorer/map_geoexplorer.css" %}" rel="stylesheet"/>
<script type="text/javascript" src="{% static "geonode/js/extjs/GeoNode-mixin.js" %}"></script>
<script type="text/javascript" src="{% static "geonode/js/extjs/Geonode-CatalogueApiSearch.js" %}"></script>
<script type="text/javascript" src="{% static "geonode/js/extjs/GeoNode-GeoExplorer.js" %}"></script>
<script type="text/javascript" src="{% static "geonode/js/utils/thumbnail.js" %}"></script>
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

        {% if 'access_token' in request.session %}
        access_token: "{{request.session.access_token}}",
        {% else %}
        access_token: null,
        {% endif %}

        {% if MAPFISH_PRINT_ENABLED %}
        printService: "{{ GEOSERVER_BASE_URL }}pdf/",
        {% else %}
        printService: null,
        printCapabilities: null,
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
                app.mapPanel.map.getResolutions = function() {
                    return [156543.03390625, 78271.516953125, 39135.7584765625,
                      19567.87923828125, 9783.939619140625, 4891.9698095703125,
                      2445.9849047851562, 1222.9924523925781, 611.4962261962891,
                      305.74811309814453, 152.87405654907226, 76.43702827453613,
                      38.218514137268066, 19.109257068634033, 9.554628534317017,
                      4.777314267158508, 2.388657133579254, 1.194328566789627,
                      0.5971642833948135, 0.2985821416974067, 0.1492910708487033,
                      0.0746455354243516];
                }
                app.mapPanel.map.getServerResolutions = function() {
                      return [156543.03390625, 78271.516953125, 39135.7584765625,
                            19567.87923828125, 9783.939619140625,
                            4891.9698095703125, 2445.9849047851562,
                            1222.9924523925781, 611.4962261962891,
                            305.74811309814453, 152.87405654907226,
                            76.43702827453613, 38.218514137268066,
                            19.109257068634033, 9.554628534317017,
                            4.777314267158508, 2.388657133579254,
                            1.194328566789627, 0.5971642833948135];
                }
                app.mapPanel.map.getMaxResolution = function() {
                    return 156543.0339 * 2;
                }
                app.mapPanel.map.getNumZoomLevels  = function() {
                    return 30;
                }
                app.mapPanel.map.getMinZoom  = function() {
                    return 0;
                }
                app.mapPanel.map.getMaxZoom  = function() {
                    return 30;
                }
                app.mapPanel.map.getResolutionForZoom = function(zoom) {
                    zoom = Math.max(0, Math.min(zoom, this.getResolutions().length - 1));
                    var resolution;
                    var fractionalZoom = true;
                    if(fractionalZoom) {
                        var low = Math.floor(zoom);
                        var high = Math.ceil(zoom);
                        resolution = this.getResolutions()[low] -
                            ((zoom-low) * (this.getResolutions()[low]-this.getResolutions()[high]));
                    } else {
                        resolution = this.getResolutions()[Math.round(zoom)];
                    }
                    return resolution;
                }
                app.mapPanel.map.adjustZoom  = function(zoom) {
                    var maxResolution = 156543.0339 * 2;
                    if (this.baseLayer && this.baseLayer.wrapDateLine) {
                        var resolution, resolutions = this.getResolutions(),
                            // maxResolution = this.getMaxExtent().getWidth() / this.size.w;
                            maxResolution = this.getMaxResolution();
                        if (this.getResolutionForZoom(zoom) > maxResolution) {
                            var fractionalZoom = true;
                            if (fractionalZoom) {
                                zoom = this.getZoomForResolution(maxResolution);
                            } else {
                                for (var i=zoom|0, ii=resolutions.length; i<ii; ++i) {
                                    if (resolutions[i] <= maxResolution) {
                                        zoom = i;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    return zoom;
                }

                try {
                    l = app.selectedLayer.getLayer();
                    l.addOptions({wrapDateLine:true, displayOutsideMaxExtent: true});
                    l.addOptions({maxExtent:app.mapPanel.map.getMaxExtent()});
                } catch(err) {
                    ;
                }

                {% if 'access_token' in request.session %}
                    try {
                        if(l.url != undefined && (typeof l.url) == "string") {
                            l.url += ( !l.url.match(/\b\?/gi) || l.url.match(/\b\?/gi).length == 0 ? '?' : '&');
                            if((!l.url.match(/\baccess_token/gi))) {
                                l.url += "access_token={{request.session.access_token}}";
                            } else {
                                l.url =
                                    l.url.replace(/(access_token)(.+?)(?=\&)/, "$1={{request.session.access_token}}");
                            }
                        }
                    } catch(err) {
                        console.log(err);
                    }
                {% endif %}

                for (var ll in app.mapPanel.map.layers) {
                    l = app.mapPanel.map.layers[ll];
                    if (l.url != undefined && (typeof l.url) == "string" && l.url.indexOf('{{GEOSERVER_BASE_URL}}') !== -1) {
                        l.addOptions({wrapDateLine:true, displayOutsideMaxExtent: true});
                        l.addOptions({maxExtent:app.mapPanel.map.getMaxExtent()});
                        {% if 'access_token' in request.session %}
                            try {
                                l.url += ( !l.url.match(/\b\?/gi) || l.url.match(/\b\?/gi).length == 0 ? '?' : '&');
                                if((!l.url.match(/\baccess_token/gi))) {
                                    l.url += "access_token={{request.session.access_token}}";
                                } else {
                                    l.url =
                                        l.url.replace(/(access_token)(.+?)(?=\&)/, "$1={{request.session.access_token}}");
                                }
                            } catch(err) {
                                console.log(err);
                            }
                        {% endif %}
                    }
                }

                var map = app.mapPanel.map;
                var layer = app.map.layers.slice(-1)[0];
                var bbox = layer.bbox;
                var crs = layer.srs;
                if (bbox != undefined)
                {
                   var extent = new OpenLayers.Bounds();

                   if (layer.capability.bbox &&
                            !Array.isArray(layer.capability.bbox) &&
                                    map.projection in layer.capability.bbox) {
                       bbox = layer.capability.bbox[map.projection].bbox;
                       extent = OpenLayers.Bounds.fromArray(bbox);
                   } else {
                       if (crs != map.projection) {
                           extent = OpenLayers.Bounds.fromArray(bbox);
                           extent = extent.clone().transform(crs, map.projection);
                       } else {
                           extent = OpenLayers.Bounds.fromArray(bbox);
                       }
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
