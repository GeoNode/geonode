/**
 * Created by
 * User: mbertrand
 * Date: 6/13/11
 * Time: 8:16 AM
 *
 */


/** api: (extends)
 *  plugins/ArcRestSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: ArcRestSource(config)
 *
 *    Plugin for using ArcGIS REST layers with :class:`gxp.Viewer` instances.
 *
 */

gxp.plugins.ArcGISCacheSource = Ext.extend(gxp.plugins.ArcRestSource, {

    /** api: ptype = gxp_arcrestcachesource */
    ptype:"gxp_arcgiscachesource",

    /** api: config[noLayersTitle]
     *  ``String``
     *  Title for no layers message (i18n).
     */
    noLayersTitle: "No ArcGIS Layers",
    
    /** api: config[noLayersText]
     *  ``String``
     *  Content of no layers message (i18n).
     */
    noLayersText: "Could not find any layers with a compatible projection (Web Mercator) at ",
    
    requiredProperties: ["name", "fullExtent", "tileInfo"],

    constructor:function (config) {
        this.config = config;
        gxp.plugins.ArcGISCacheSource.superclass.constructor.apply(this, arguments);
    },


    /** private: method[createStore]
     *
     *  Creates a store of layers.  This requires that the API script has already
     *  loaded.  Fires the "ready" event when the store is loaded.
     */
    createStore:function () {
        var baseUrl = this.url.split("?")[0].replace(/https?:/,window.location.protocol);
        var source = this;

        var processResult = function (response) {
            var json = Ext.decode(response.responseText);
            var layerProjection = source.getArcProjection(json.spatialReference.wkid);
            var layers=[];
            if (layerProjection != null) {
                    layers.push(new OpenLayers.Layer.ArcGISCache(json.layers[0].name, baseUrl,
                        {
                            layerInfo: json
                        },
                        {
                            isBaseLayer:false,
                            ratio: 1,
                            displayInLayerSwitcher:true,
                            visibility:true,
                            projection:layerProjection,
                            queryable:json.capabilities && json.capabilities.indexOf("Identify") > -1}
                    ));

            }  else {
                processFailure(response);
            }
            source.title = json.documentInfo.Title;

            source.store = new GeoExt.data.LayerStore({
               layers:layers,
               fields:[
                    	        {name:"source", type:"string"},
                    	        {name:"name", type:"string", mapping:"name"},
                    	        {name:"layerid", type:"string"},
                    	        {name:"group", type:"string", defaultValue:"background"},
                    	        {name:"fixed", type:"boolean", defaultValue:true},
                    	        {name:"tiled", type:"boolean", defaultValue:true},
                    	        {name:"queryable", type:"boolean", defaultValue:true},
                    	        {name:"selected", type:"boolean"}
                    	        ]
                    });
            
            source.fireEvent("ready", source);

        };

        var processFailure = function (response) {
        	if (!response.isTimeout) {
        		Ext.Msg.alert(source.noLayersTitle, source.noLayersText + source.config.url);
        	}	
            source.fireEvent("failure", source);
        };


        this.lazy = this.isLazy();

        if (!this.lazy) {
            Ext.Ajax.request({
                url:baseUrl,
                timeout: 2000,
                params:{'f':'json', 'pretty':'false', 'keepPostParams':'true'},
                method:'POST',
                success:processResult,
                failure:processFailure
            });
        } else {
            this.fireEvent("ready");
        }
    },

    /** api: method[getConfigForRecord]
     *  :arg record: :class:`GeoExt.data.LayerRecord`
     *  :returns: ``Object``
     *
     *  Create a config object that can be used to recreate the given record.
     */
    createLayerRecord:function (config) {
        var record, layer;
        var cmp = function (l) {
            return l.get("name") === config.name;
        };

        var recordExists = this.lazy ||  (this.store && this.store.findBy(cmp) > -1);

        // only return layer if app does not have it already
        if (this.target.mapPanel.layers.findBy(cmp) == -1 && recordExists) {
            // records can be in only one store

            if (!this.lazy &&  this.store.findBy(cmp) > -1 ) {
                record = this.store.getAt(this.store.findBy(cmp)).clone();
            } else {
                record = this.createLazyLayerRecord(config);
            }
            layer = record.getLayer();

            // set layer title from config
            if (config.title) {
                layer.setName(config.title);
                record.set("title", config.title);
            }
            // set visibility from config
            if ("visibility" in config) {
                layer.visibility = config.visibility;
            }

            if ("opacity" in config) {
                layer.opacity = config.opacity;
            }

            if ("format" in config) {
                layer.params.FORMAT = config.format;
                record.set("format", config.format);
            }

            var singleTile = false;
            if ("tiled" in config) {
                singleTile = !config.tiled;
            } 
            
            record.set("name", config.name);
            record.set("layerid", config.layerid || "show:0");
            record.set("format", config.format || "png");
            
            record.set("tiled", !singleTile);
            record.set("selected", config.selected || false);
            record.set("queryable", config.queryable || true);
            record.set("source", config.source);


            record.set("properties", "gxp_wmslayerpanel");  
            
            if ("group" in config) {
                record.set("group", config.group);
            }
            
            record.commit();
        }
        return record;
    },    

    /** private: method[createLazyLayerRecord]
     *  :arg config: ``Object`` The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a minimal layer record
     */
    createLazyLayerRecord: function(config) {
        var srs = config.srs || this.target.map.projection;
        config.srs = {};
        config.srs[srs] = true;

        var bbox = config.bbox || this.target.map.maxExtent || OpenLayers.Projection.defaults[srs].maxExtent;
        config.bbox = {};
        config.bbox[srs] = {bbox: bbox};

        var  record = new GeoExt.data.LayerRecord(config);        
        var info = {
        		"fullExtent": config.fullExtent,
        		"spatialReference":{"wkid": srs},
        		"tileInfo": config.tileInfo
        };

        record.setLayer(new OpenLayers.Layer.ArcGISCache(config.name,  this.url.split("?")[0],
            {
                layerInfo: info
            },
            {
                isBaseLayer:false,
                displayInLayerSwitcher:true,
                projection:srs,
                singleTile: "tiled" in config ? !config.tiled : false,
                queryable: "queryable" in config ? config.queryable : false}
        )
        );
        return record;

    },
    


    /** api: method[getConfigForRecord]
     *  :arg record: :class:`GeoExt.data.LayerRecord`
     *  :returns: ``Object``
     *
     *  Create a config object that can be used to recreate the given record.
     */
    getConfigForRecord: function(record) {
        var layer = record.getLayer();
        return {
            source: record.get("source"),
            name: record.get("name"),
            title: record.get("title"),
            tiled: record.get("tiled"),
            visibility: layer.getVisibility(),
            layerid: layer.params.LAYERS,
            format: layer.params.FORMAT,
            opacity: layer.opacity || undefined,
            group: record.get("group"),
            fixed: record.get("fixed"),
            selected: record.get("selected")
            // Just get the following from ESRI, don't save it all to GeoNode
            //fullExtent: layer.layerInfo.fullExtent,
            //tileInfo: layer.layerInfo.tileInfo
        };
    }    
    
});

Ext.preg(gxp.plugins.ArcGISCacheSource.prototype.ptype, gxp.plugins.ArcGISCacheSource);
