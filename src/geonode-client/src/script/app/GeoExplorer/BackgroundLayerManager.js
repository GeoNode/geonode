/**
 * Copyright (c) 2009 The Open Planning Project
 */

/**
 *
 */
GeoExplorer.BackgroundLayerManager = Ext.extend(Ext.util.Observable, {
    backgroundQueue: null,
    backgroundLayers: null, 

    // i18n defaults
    backgroundDisabledText: "UT: No background",

    constructor: function(config) {
        this.initialConfig = config;
        Ext.apply(this, this.initialConfig);
        this.backgroundQueue = [];
    },

    /**
     * Create an array of loader functions, such as might be passed to
     * gxp.util.dispatch().  The loader functions prepare this
     * BackgroundLayerManager to provide the background layers described in its
     * configuration.
     */
    getBackgroundLoaders: function () {
        var loaders = [];

        var proxy = this.proxy;
        function mungeSourcePlugin(conf) {
            var ptype =
                "service" in conf ? "gx-" + conf.service + "source" : "gx-wmssource";
            var pluginConfig = { "ptype": ptype };
            Ext.apply(pluginConfig, conf);

            if (proxy !== undefined &&
                "url" in pluginConfig && 
                pluginConfig.url.startsWith("http")
            ) {
                pluginConfig.url = proxy + escape(pluginConfig.url);
            }

            delete pluginConfig.service;
            delete pluginConfig.layers;
            return pluginConfig;
        }

        function backgroundLayerAdder(source, conf) {
            return function(done) {
                source.on({
                    "ready": done,
                    "scope": this
                });
                source.init(this);
            }
        }

        for (var i = 0, len = this.backgroundLayers.length; i < len; i++) {
            var conf = this.backgroundLayers[i];
            var pluginConf = mungeSourcePlugin(conf);
            var source = Ext.ComponentMgr.createPlugin(pluginConf, "gx-wmssource");
            this.backgroundQueue.push({"source": source, "conf": conf});
            loaders.push(backgroundLayerAdder(source, conf));
        }

        return loaders;
    },

    getBackgroundLayers: function () {
        var bglayers = []
        var visible = true;
        for (var i = 0, len = this.backgroundQueue.length; i < len; i++) {
            var source = this.backgroundQueue[i].source;
            var layers = this.backgroundQueue[i].conf.layers;
            for (var j = 0, jlen = layers.length; j < jlen; j++) {
                var conf = layers[j];
                if ((typeof conf) === "string") conf = {"name": conf};
                conf.isBaseLayer = true;
                conf.visibility = visible;

                var layer = source.createLayerRecord(conf);
                layer.set("group", "background");
                layer.get("layer").visibility = visible; 
                // visibility from config is not respected for Google layers

                visible = false;
                bglayers.push(layer);
            }
        }

        bglayers.push(new GeoExt.data.LayerRecord({
            title: this.backgroundDisabledText,
            layer: new OpenLayers.Layer(this.backgroundDisabledText, {
                'visibility': false
            }),
            group: "background",
            queryable: 'false'
        }));

        return bglayers;
    }
});
