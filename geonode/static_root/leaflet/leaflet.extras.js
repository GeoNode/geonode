L.Control.ResetView = L.Control.extend({
    statics: {
        ICON: 'url(images/reset-view.png)',
        TITLE: "Reset view"
    },

    options: {
        position: 'topleft'
    },

    initialize: function (bounds, options) {
        // Accept function as argument to bounds
        this.getBounds = typeof(bounds) == 'function' ? bounds :
                                                        function() { return bounds; };

        L.Util.setOptions(this, options);
    },

    onAdd: function (map) {
        if (map.resetviewControl) {
            map.removeControl(map.resetviewControl);
        }
        map.resetviewControl = this;

        var container = L.DomUtil.create('div', 'leaflet-control-zoom leaflet-bar');
        var link = L.DomUtil.create('a', 'leaflet-control-zoom-out leaflet-bar-part', container);
        link.href = '#';
        link.title = L.Control.ResetView.TITLE;
        link.style.backgroundImage = L.Control.ResetView.ICON;

        L.DomEvent.addListener(link, 'click', L.DomEvent.stopPropagation)
                  .addListener(link, 'click', L.DomEvent.preventDefault)
                  .addListener(link, 'click', L.Util.bind(function() {
                      map.fitBounds(this.getBounds());
                   }, this));
        return container;
    }
});


L.Map.DjangoMap = L.Map.extend({

    initialize: function (id, options) {
        // Merge compatible options
        // (can be undefined)
        var djoptions = options.djoptions;
        options.zoom = djoptions.zoom;
        options.center = djoptions.center;
        options.minZoom = djoptions.minzoom;
        options.maxZoom = djoptions.maxzoom;
        // Translate to native options
        options = L.Util.extend(options,
                                this._projectionOptions(djoptions));
        if (djoptions.extent) {
            options.maxBounds = djoptions.extent;
        }

        L.Map.prototype.initialize.call(this, id, options);

        this._djAddLayers();
        this._djSetupControls();

        if (djoptions.fitextent && djoptions.extent &&
            !(djoptions.center || djoptions.zoom)) {
            this.fitBounds(options.maxBounds);
        }
    },

    _projectionOptions: function (djoptions) {
        if (!djoptions.srid)
            return {};

        var projopts = {};

        var bbox = djoptions.tilesextent,
            maxResolution = computeMaxResolution(bbox);
        // See https://github.com/ajashton/TileCache/blob/master/tilecache/TileCache/Layer.py#L197
        var resolutions = [];
        for(var z=0; z<20; z++) {
            resolutions.push(maxResolution / Math.pow(2, z));
        }
        var crs = new L.Proj.CRS('EPSG:' + djoptions.srid,
                                 Proj4js.defs['EPSG:' + djoptions.srid],
                                 {origin: [bbox[0], bbox[3]],
                                  resolutions: resolutions});
        return {
            crs: crs,
            scale: crs.scale,
            continuousWorld: true
        };

        function computeMaxResolution(bbox) {
            // See https://github.com/ajashton/TileCache/blob/master/tilecache/TileCache/Layer.py#L185-L196
            var size = 256,
                width  = bbox[2] - bbox[0],
                height = bbox[3] - bbox[1];
            var aspect = Math.floor(Math.max(width, height) / Math.min(width, height) + 0.5);
            return Math.max(width, height) / (size * aspect);
        }
    },

    _djAddLayers: function () {
        var layers = this.options.djoptions.layers,
            continuousWorld = this.options.continuousWorld;

        if (layers.length == 1) {
            var layer = l2d(layers[0]);
            L.tileLayer(layer.url, layer.options).addTo(this);
            return;
        }

        this.layerscontrol = L.control.layers().addTo(this);
        for (var i = 0, n = layers.length; i < n; i++) {
            var layer = l2d(layers[i]),
                l = L.tileLayer(layer.url, layer.options);
            this.layerscontrol.addBaseLayer(l, layer.name);
            // Show first one as default
            if (i === 0) l.addTo(this);
        }

        function l2d(l) {
            var options = {'attribution': l[2],
                           'continuousWorld': continuousWorld};
            return {name: l[0], url: l[1], options: options};
        }
    },

    _djSetupControls: function () {
        // Attribution prefix ?
        if (this.attributionControl &&
            this.options.djoptions.attributionprefix !== null) {
            this.attributionControl.setPrefix(this.options.djoptions.attributionprefix);
        }

        // Scale control ?
        if (this.options.djoptions.scale) {
            this.whenReady(function () {
                var scale_opt = this.options.djoptions.scale;
                var show_imperial = /both|imperial/.test(scale_opt);
                var show_metric = /both|metric/.test(scale_opt);
                new L.Control.Scale({imperial: show_imperial, metric: show_metric}).addTo(this);
            }, this);
        }

        // Minimap control ?
        if (this.options.djoptions.minimap) {
            for (var firstLayer in this._layers) break;
            var url = this._layers[firstLayer]._url;
            var layer = L.tileLayer(url);
            this.minimapcontrol = null;
            this.whenReady(function () {
                this.minimapcontrol = new L.Control.MiniMap(layer,
                                                            {toggleDisplay: true}).addTo(this);
            }, this);
        }

        // ResetView control ?
        if (this.options.djoptions.resetview) {
            var bounds = this.options.djoptions.extent;
            if (bounds) {
                // Add reset view control
                this.whenReady(function () {
                    new L.Control.ResetView(bounds).addTo(this);
                }, this);
            }
        }
    }

});


L.Map.djangoMap = function (id, options) {
    var container = L.DomUtil.get(id);
    if (container._leaflet)  // Already initialized
        return;

    var map = new L.Map.DjangoMap(id, options);

    if (options.globals) {
        // Register document maps, like window.forms :)
        window.maps = window.maps || [];
        window.maps.push(map);
    }

    if (options.callback === null) {
        /*
         * Deprecate django-leaflet < 0.7 default callback
         */
        var defaultcb = window[id + 'Init'];
        if (typeof(defaultcb) == 'function') {
            options.callback = defaultcb;
            if (console) console.warn('DEPRECATED: Use of default callback ' + defaultcb.name + '() is deprecated (see documentation).');
        }
    }

    /*
     * Trigger custom map:init Event
     */
    triggerEvent(window, 'map:init', {map: map, options: options});

    /*
     * Run callback if specified
     */
    if (typeof(options.callback) == 'function') {
        setTimeout(function () {
            options.callback(map, options);
        }, 0);
    }

    return map;


    function triggerEvent(target, type, data) {
        if (typeof window.CustomEvent == 'function') {
            var evt = new CustomEvent(type, {detail: data});
            target.dispatchEvent(evt);
        }
        else if (window.jQuery) {
            var evt = jQuery.Event(type);
            evt.detail = data;
            jQuery(target).trigger(evt);
        }
    }
};
