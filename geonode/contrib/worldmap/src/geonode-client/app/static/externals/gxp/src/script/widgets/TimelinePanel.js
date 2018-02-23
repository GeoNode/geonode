/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires util.js
 * @requires widgets/tips/RangeSliderTip.js
 * @requires widgets/FeatureEditPopup.js
 * @requires OpenLayers/Format/SLD/v1_0_0.js
 * @requires OpenLayers/Renderer/SVG.js
 * @requires OpenLayers/Renderer/VML.js
 * @requires OpenLayers/Renderer/Canvas.js
 * @requires OpenLayers/Layer/Vector.js
 * @requires OpenLayers/Strategy/BBOX.js
 * @requires OpenLayers/Filter/Logical.js
 * @requires OpenLayers/Filter/Comparison.js
 * @requires OpenLayers/Protocol/WFS/v1_1_0.js
 * @requires OpenLayers/BaseTypes/Date.js
 * @requires OpenLayers/BaseTypes/LonLat.js
 * @requires OpenLayers/Filter/Spatial.js
 */

/** api: (define)
 *  module = gxp
 *  class = TimelinePanel
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

// showBy does not allow offsets
Ext.override(Ext.Tip, {
    showBy: function(el, pos, offsets){
        var offsetX = offsets[0];
        var offsetY = offsets[1];
        if (pos.charAt(0) === 'b') {
            offsetY = -offsetY;
        }
        if (pos.charAt(0) === 'r' || pos.charAt(1) === 'r') {
            offsetX = -offsetX;
        }
        if (pos.charAt(0) === 'c') {
            offsetX = 0;
            offsetY = 0;
        }
        if (pos.charAt(0) === 'l' || pos.charAt(0) === 'r') {
            offsetY = 0;
        }
        if(!this.rendered){
            this.render(Ext.getBody());
        }
        this.showAt(this.el.getAlignToXY(el, pos || this.defaultAlign, [offsetX, offsetY]));
    }   
});

// TODO use from GeoExt eventually
GeoExt.FeatureTip = Ext.extend(Ext.Tip, {

    /** api: config[map]
     *  ``OpenLayers.Map``
     */
    map: null,

    /** api: config[location]
     *  ``OpenLayers.Feature.Vector``
     */
    location: null,

    /** private: method[initComponent]
     *  Initializes the feature tip.
     */
    initComponent: function() {
        var centroid = this.location.geometry.getCentroid();
        this.location = new OpenLayers.LonLat(centroid.x, centroid.y);
        this.map.events.on({
            "move" : this.show,
            scope : this
        });
        GeoExt.FeatureTip.superclass.initComponent.call(this);
    },

    /** private: method[beforeDestroy]
     *  Cleanup events before destroying the feature tip.
     */
    beforeDestroy: function() {
        this.map.events.un({
            "move" : this.show,
            scope : this
        });
        GeoExt.FeatureTip.superclass.beforeDestroy.call(this);
    },

    /** private: method[getPosition]
     *  Get the position of the feature in pixel space.
     *
     *  :returns: ``Array`` The position of the feature in pixel space or
     *  null if the feature is not visible in the map.
     */
    getPosition: function() {
        if (this.map.getExtent().containsLonLat(this.location)) {
            var locationPx = this.map.getPixelFromLonLat(this.location),
                mapBox = Ext.fly(this.map.div).getBox(true),
                top = locationPx.y + mapBox.y,
               left = locationPx.x + mapBox.x;
            return [left, top];
        } else {
            return null;
        }
    },

    /** api: method[show]
     *  Show the feature tip.
     */
    show: function() {
        var position = this.getPosition();
        if (position !== null) {
            this.showAt(position);
        } else {
            this.hide();
        }
    }

});

// http://code.google.com/p/simile-widgets/issues/detail?id=3
window.Timeline && window.SimileAjax && (function() {
    SimileAjax.History.enabled = false;

    Timeline._Band.prototype._onDblClick = Ext.emptyFn;

    Timeline.DefaultEventSource.prototype.remove = function(id) {
        this._events.remove(id);
    };
    SimileAjax.EventIndex.prototype.remove = function(id) {
        var evt = this._idToEvent[id];
        this._events.remove(evt);
        delete this._idToEvent[id];
    };
    Timeline._Band.prototype.zoom = function(zoomIn, x, y, target) {
        if (!this._zoomSteps) {
            // zoom disabled
            return;
        }
        var center = this.getCenterVisibleDate();
        var netIntervalChange = this._ether.zoom(zoomIn);
        this._etherPainter.zoom(netIntervalChange);
        this.setCenterVisibleDate(center);
    };
})();

/** api: constructor
 *  .. class:: TimelinePanel(config)
 *   
 *      A panel for displaying a Similie Timeline.
 */
gxp.TimelinePanel = Ext.extend(Ext.Panel, {

    /** api: config[featureEditor]
     *  ``gxp.plugins.FeatureEditor``
     */

    /** private: property[featureManager]
     *  ``gxp.plugins.FeatureManager``
     */

    /** api: config[timeInfoEndpoint]
     *  ``String``
     *  url to use to get time info about a certain layer.
     */
    timeInfoEndpoint: "/maps/time_info.json?",

    /** api: config[annotationConfig]
     *  ``Object`` Configuration object for the integration of annotations
     *  with the timeline.
     */
    annotationConfig: {
        timeAttr: 'start_time',
        endTimeAttr: 'end_time',
        filterAttr: 'in_timeline',
        mapFilterAttr: 'in_map'
    },
    
    /** api: config[viewer]
     *  ``gxp.Viewer``
     */

    /** api: config[playbackTool]
     *  ``gxp.plugins.Playback``
     */

    /** private: property[timeline]
     *  ``Timeline``
     */
    
    /** private: property[timelineContainer]
     *  ``Ext.Container``
     */
    
    /** private: property[eventSource]
     *  ``Object``
     *  Timeline event source.
     */

    /** api: config[loadingMessage]
     *  ``String`` Message to show when the timeline is loading (i18n)
     */
    loadingMessage: "Loading Timeline data...",

    /** api: config[instructionText]
     *  ``String`` Message to show when there is too many data for the timeline (i18n)
     */   
    instructionText: "There are too many events ({count}) to show in the timeline.<br/>Please zoom in or move the vertical slider down (maximum is {max})",

    /** api: config[errorText]
     *  ``String`` Message to show when there is an exception when retrieving the WFS data (i18n)
     */
    errorText: "Something went wrong with retrieving the data for the timeline",

    /** private: property[layerCount]
     * ``Integer`` The number of vector layers currently loading.
     */
    layerCount: 0,

    /**
     * private: property[busyMask]
     * ``Ext.LoadMask`` The Ext load mask to show when busy.
     */
    busyMask: null,

    /** api: property[schemaCache]
     *  ``Object`` An object that contains the attribute stores.
     */
    schemaCache: {},

    /** api: property[propertyNamesCache]
     *  ``Object`` An object that contains the property names to query for.
     *  This should be all attributes except the geometry.
     */
    propertyNamesCache: {},

    /** private: property[sldCache]
     *  ``Object`` An object that contains the parsed SLD documents.
     */
    sldCache: {},

    /** api: property[layerLookup]
     *  ``Object``
     *  Mapping of store/layer names (e.g. "local/foo") to objects storing data
     *  related to layers.  The values of each member are objects with the 
     *  following properties:
     *
     *   * layer - {OpenLayers.Layer.Vector}
     *   * titleAttr - {String}
     *   * timeAttr - {String}
     *   * endTimeAttr - {String}
     *   * filterAttr - {String}
     *   * visible - {Boolean}
     *   * timeFilter - {OpenLayers.Filter}
     *   * sldFilter - {OpenLayers.Filter}
     *   * clientSideFilter - {OpenLayers.Filter}
     *  
     */
    
    /** private: property[rangeInfo]
     *  ``Object`` An object with 2 properties: current and original.
     *  Current contains the original range with a fraction on both sides.
     */

    /**
     * api: config[maxFeatures]
     * ``Integer``
     * The maximum number of features in total for the timeline.
     */
    maxFeatures: 500,

    /**
     * api: config[bufferFraction]
     * ``Float``
     * The fraction to take around on both sides of a time filter. Defaults to 1.
     */
    bufferFraction: 1,

    layout: "border",

    /** private: method[initComponent]
     */
    initComponent: function() {

        // handler for clicking on an event in the timeline
        Timeline.OriginalEventPainter.prototype._showBubble = 
            this.handleEventClick.createDelegate(this);

        this.timelineContainer = new Ext.Container({
            region: "center"
        });

        this.eventSource = new Timeline.DefaultEventSource(0);

        this.items = [{
            region: "west",
            xtype: "container",
            layout: "vbox",
            margins: "10 5",
            width: 20,
            items: [{
                xtype: "panel",
                margins: "3 1",
                cls: "x-tool x-tool-minus",
                listeners: {
                    afterrender: function(c){ 
                        c.getEl().on('click', function() {
                            var value = this.rangeSlider.getValue();
                            this.rangeSlider.setValue(0, value+10, true, true);
                        }, this);
                    },
                    scope: this
                }
           }, {
                xtype: "slider",
                ref: "../rangeSlider",
                vertical: true,
                flex: 1,
                value: 25,
                minValue: 1,
                maxValue: 100,
                listeners: {
                    "change": this.onChange,
                    "changecomplete": this.onChangeComplete,
                    scope: this
                },
                plugins: [new gxp.slider.RangeSliderTip()]
            }, {
                xtype: "panel",
                margins: "3 1",
                cls: "x-tool x-tool-plus",
                listeners: {
                    afterrender: function(c){ 
                        c.getEl().on('click', function() {
                            var value = this.rangeSlider.getValue();
                            this.rangeSlider.setValue(0, value-10, true, true);
                        }, this);
                    },
                    scope: this
                }
            }]
        }, this.timelineContainer
        ];

        // we are binding with viewer to get updates on new layers        
        if (this.initialConfig.viewer) {
            delete this.viewer;
            this.bindViewer(this.initialConfig.viewer);
        }

        // we are binding with a feature editor to get notes/annotations
        if (this.initialConfig.featureEditor) {
            delete this.featureEditor;
            this.bindFeatureEditor(this.initialConfig.featureEditor);
        }

        // we are binding with the playback tool to get updates on ranges
        // and current times
        if (this.initialConfig.playbackTool) {
            delete this.playbackTool;
            this.bindPlaybackTool(this.initialConfig.playbackTool);
        }

        if (this.ownerCt) {
            this.ownerCt.on("beforecollapse", function() {
                this._silentMapMove = true;
            }, this);
            this.ownerCt.on("beforeexpand", function() {
                delete this._silentMapMove;
            }, this);
            this.ownerCt.on("afterlayout", function() {
                delete this._silent;
            }, this);
        }

        gxp.TimelinePanel.superclass.initComponent.call(this); 
    },

    /**
     * private: method[onChange]
     *  :arg slider: ``Ext.Slider``
     *  :arg value: ``Float``
     *
     *  Event listener for when the vertical slider is moved. Update the
     *  range slider's tooltip.
     */
    onChange: function(slider, value, thumb) {
        // TODO this logic needs to be more centralized, it's now in several places
        var range = this.playbackTool.playbackToolbar.control.range;
        range = this.calculateNewRange(range, value);
        var start = new Date(range[0].getTime() - this.bufferFraction * (range[1] - range[0]));
        var end = new Date(range[1].getTime() + this.bufferFraction * (range[1] - range[0]));
        // don't go beyond the original range
        start = new Date(Math.max(this.originalRange[0], start));
        end = new Date(Math.min(this.originalRange[1], end));
        this.updateRangeSlider([start, end]);
    },

    /**
     * private: method[onChangeComplete]
     *  :arg slider: ``Ext.Slider``
     *  :arg value: ``Float``
     *
     *  Event listener for when the vertical slider is moved. This will
     *  influence the date range which will be used in the WFS protocol.
     */
    onChangeComplete: function(slider, value) {
        if (this.playbackTool) {
            var range = this.playbackTool.playbackToolbar.control.range;
            range = this.calculateNewRange(range, value);
            // correct for movements of the timeline in the mean time
            var center = this.playbackTool.playbackToolbar.control.currentTime;
            var span = range[1]-range[0];
            var start = new Date(center.getTime() - span/2);
            var end = new Date(center.getTime() + span/2);
            for (var key in this.layerLookup) {
                var layer = this.layerLookup[key].layer;
                layer && this.setTimeFilter(key, this.createTimeFilter([start, end], key, this.bufferFraction));
            }
            this.updateTimelineEvents({force: true});
        }
    },

    /**
     * private: method[setFilterMatcher]
     *  :arg filterMatcher: ``Function``
     *
     *  Filter data in the timeline and repaint.
     */
    setFilterMatcher: function(filterMatcher) {
        if (this.timeline) {
            this.timeline.getBand(0).getEventPainter().setFilterMatcher(filterMatcher);
            this.timeline.getBand(1).getEventPainter().setFilterMatcher(filterMatcher);
            this.timeline.paint();
        }
    },

    /**
     * api: method[setLayerVisibility]
     *  :arg item: ``Ext.Menu.CheckItem``
     *  :arg checked: ``Boolean``
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg clear: ``Boolean``
     *
     *  Change the visibility for a layer which is shown in the timeline.
     */
    setLayerVisibility: function(item, checked, record, clear) {
        var keyToMatch = this.getKey(record);
        (clear !== false) && this.clearEventsForKey(keyToMatch);
        Ext.apply(this.layerLookup[keyToMatch], {
            visible: checked
        });
        var filterMatcher = function(evt) {
            var key = evt.getProperty('key');
            if (key === keyToMatch) {
                return checked;
            } else {
                return true;
            }
        };
        this.setFilterMatcher(filterMatcher);
        this.updateTimelineEvents();
    },

    /**
     * api: method[applyFilter]
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg filter: ``OpenLayers.Filter``
     *  :arg checked: ``Boolean``
     *
     *  Filter a layer which is shown in the timeline.
     */
    applyFilter: function(record, filter, checked) {
        var key = this.getKey(record);
        var layer = this.layerLookup[key].layer;
        if (checked) {
            this.layerLookup[key].clientSideFilter = filter;
        } else {
            delete this.layerLookup[key].clientSideFilter;
        }
        if (this.layerLookup[key].layer) {
            this.layerLookup[key].layer.filter = this.assembleFullFilter(key);
        }
        this.updateTimelineEvents({force: true});
    },

    /**
     * api: method[setTitleAttribute]
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg titleAttr: ``String``
     *
     *  Change the attribute to show in the timeline for a certain layer.
     *  Currently this means removing all features and re-adding them.
     */
    setTitleAttribute: function(record, titleAttr) {
        var key = this.getKey(record);
        this.layerLookup[key].titleAttr = titleAttr;
        this.clearEventsForKey(key);
        this.onFeaturesAdded({features: this.layerLookup[key].layer.features}, key);
    },

    /**
     * private method[destroyPopup]
     *
     *  Destroy an existing popup.
     */
    destroyPopup: function() {
        if (this.popup) {
            this.popup.destroy();
            this.popup = null;
        }
    },

    /**
     * private: method[handleEventClick]
     *  :arg x: ``Integer``
     *  :arg y: ``Integer``
     *  :arg evt: ``Object``
     *  
     *  Handler for when an event in the timeline gets clicked. Show a popup
     *  for a feature and the feature editor for a note/annotation.
     */
    handleEventClick: function(x, y, evt) {
        var fid = evt.getProperty("fid");
        var key = evt.getProperty("key");
        var layer = this.layerLookup[key].layer;
        var feature = layer && layer.getFeatureByFid(fid);
        if (feature) {
            this.destroyPopup();
            // if annotations, show feature editor
            if (!layer.protocol) {
                if (this.featureEditor) { 
                    this.featureEditor._forcePopupForNoGeometry = true;
                    layer.events.triggerEvent("featureselected", {feature: feature});
                    delete this.featureEditor._forcePopupForNoGeometry;
                }
            } else {
                if (!feature.geometry && feature.bounds) {
                    feature.geometry = feature.bounds.toGeometry();
                }
                var centroid = feature.geometry.getCentroid();
                var map = this.viewer.mapPanel.map;
                this._silentMapMove = true;
                map.setCenter(new OpenLayers.LonLat(centroid.x, centroid.y));
                delete this._silentMapMove;
                this.popup = new gxp.FeatureEditPopup({
                    feature: feature,
                    propertyGridNameText: "Attributes",
                    title: evt.getProperty("title"),
                    panIn: false,
                    width: 200,
                    height: 250,
                    collapsible: true,
                    readOnly: true,
                    hideMode: 'offsets'
                });
                this.popup.show();
            }
        }
    },

    /**
     * private: method[bindFeatureEditor]
     *  :arg featureEditor: ``gxp.plugins.FeatureEditor``
     *  
     *  Bind with a feature editor to have notes show up in the timeline.
     */
    bindFeatureEditor: function(featureEditor) {
        this.featureEditor = featureEditor;
        this.featureManager = featureEditor.getFeatureManager();
        this.featureManager.on("layerchange", this.onLayerChange, this);
    },

    /**
     * private: method[unbindFeatureEditor]
     *  
     *  Unbind with a feature editor and its associated feature manager.
     */
    unbindFeatureEditor: function() {
        if (this.featureManager) {
            if (this.featureManager.featureStore) {
                this.featureManager.featureStore.un("write", this.onSave, this);
            }
            this.featureManager.un("layerchange", this.onLayerChange, this);
            this.featureManager = null;
        }
        this.featureEditor = null;
    },

    /**
     * private: method[guessTitleAttribute]
     *  :arg schema: ``GeoExt.data.AttributeStore``
     *  :returns: ``String``
     *
     *  Find the first string attribute and use that to show events in the
     *  timeline.
     */
    guessTitleAttribute: function(schema) {
        var titleAttr = null;
        schema.each(function(record) {
            if (record.get("type") === "xsd:string") {
                titleAttr = record.get("name");
                return false;
            }           
        });
        return titleAttr;
    },

    /**
     * private: method[onLayerChange]
     *  :arg tool: ``gxp.plugins.FeatureManager``
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg schema: ``GeoExt.data.AttributeStore``
     *
     *  Listener for when the layer record associated with the feature manager
     *  changes. When this is fired, we can hook up the notes to the timeline.
     */
    onLayerChange: function(tool, record, schema) {
        var key = this.getKey(record);
        var titleAttr = this.guessTitleAttribute(schema);
        var layer = this.featureManager.featureLayer;
        this.layerLookup[key] = Ext.apply({
            titleAttr: titleAttr,
            icon: Timeline.urlPrefix + "/images/note.png",
            layer: layer,
            visible: true
        }, this.annotationConfig);
        this.featureManager.on("query", function(tool, store) {
            var features = [];
            store.each(function(record) {
                features.push(record.getFeature());
            });
            this.addFeatures(key, features);
        }, this, {single: true});
        if (this.featureManager.featureStore) {
            // we cannot use the featureLayer's events here, since features
            // will be added without attributes
            this.featureManager.featureStore.on("write", this.onSave, this);
        }
        this.annotationsRecord = record;
    },

    /**
     * private: method[onSave]
     *  :arg store: ``gxp.data.WFSFeatureStore``
     *  :arg action: ``String``
     *  :arg data: ``Array``
     *
     *  When annotation features are saved to the store, we can add them to
     *  the timeline.
     */
    onSave: function(store, action, data) {
        var key = this.getKey(this.annotationsRecord);
        var features = [];
        for (var i=0, ii=data.length; i<ii; i++) {
            var feature = data[i].feature;
            features.push(feature);
            var fid = feature.fid;
            this.clearEventsForFid(key, fid);
            if (this.tooltips && this.tooltips[fid]) {
                this.tooltips[fid].destroy();
                this.tooltips[fid] = null;
            }
        }
        if (action !== Ext.data.Api.actions.destroy) {
            this.addFeatures(key, features);
        }
        this.showAnnotations(this.playbackTool.playbackToolbar.control.currentTime);
    },

    /**
     * private: method[bindPlaybackTool]
     *  :arg playbackTool: ``gxp.plugins.Playback``
     *
     *  Bind with the playback tool so we get updates on when we have to move
     *  the timeline and when we have to change the range.
     */
    bindPlaybackTool: function(playbackTool) {
        this.playbackTool = playbackTool;
        this.playbackTool.on("timechange", this.onTimeChange, this);
        this.playbackTool.on("rangemodified", this.onRangeModify, this);
    },

    /**
     * private: method[unbindPlaybackTool]
     *
     *  Unbind with the playback tool
     */
    unbindPlaybackTool: function() {
        if (this.playbackTool) {
            this.playbackTool.un("timechange", this.onTimeChange, this);
            this.playbackTool.un("rangemodified", this.onRangeModify, this);
            this.playbackTool = null;
        }
    },

    /**
     * private: method[onTimeChange]
     *  :arg toolbar: ``gxp.plugin.PlaybackToolbar``
     *  :arg currentTime: ``Date``
     *
     *  Listener for when the playback tool fires timechange.
     */
    onTimeChange: function(toolbar, currentTime) {
        this._silent = true;
        this._ignoreTimeChange !== true && this.setCenterDate(currentTime);
        delete this._silent;
    },

    /** private: method[onRangeModify]
     *  :arg toolbar: ``gxp.plugin.PlaybackToolbar``
     *  :arg range: ``Array(Date)``
     *
     *  Listener for when the playback tool fires rangemodified
     */
    onRangeModify: function(toolbar, range) {
        this._silent = true;
        this.setRange(range);
        delete this._silent;
    },

    /** private: method[createTimeline]
     *  :arg range:  ``Array``
     *
     *  Create the Simile timeline object.
     */
    createTimeline: function(range) {
        if (!this.rendered || (this.timelineContainer.el.getSize().width === 0 && this.timelineContainer.el.getSize().height === 0)) {
            return;
        }
        var theme = Timeline.ClassicTheme.create();
        var span = range[1] - range[0];
        var years  = ((((span/1000)/60)/60)/24)/365;
        var intervalUnits = [];
        if (years >= 50) {
            intervalUnits.push(Timeline.DateTime.DECADE);
            intervalUnits.push(Timeline.DateTime.CENTURY);
        } else {
            intervalUnits.push(Timeline.DateTime.YEAR);
            intervalUnits.push(Timeline.DateTime.DECADE);
        }
        var d = new Date(range[0].getTime() + span/2);
        var bandInfos = [
            Timeline.createBandInfo({
                width: "80%", 
                intervalUnit: intervalUnits[0], 
                intervalPixels: 200,
                eventSource: this.eventSource,
                date: d,
                theme: theme,
                layout: "original",
                zoomIndex: 7,
                zoomSteps: [
                    {pixelsPerInterval: 25,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 50,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 75,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 100,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 125,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 150,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 175,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 200,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 225,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 250,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 275,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 300,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 325,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 350,  unit: intervalUnits[0]},
                    {pixelsPerInterval: 375,  unit: intervalUnits[0]}
                ]
            }),
            Timeline.createBandInfo({
                width: "20%", 
                intervalUnit: intervalUnits[1], 
                intervalPixels: 200,
                eventSource: this.eventSource,
                date: d,
                theme: theme,
                layout: "overview"
            })
        ];
        bandInfos[1].syncWith = 0;
        bandInfos[1].highlight = true;

       bandInfos[0].decorators = [
            new Timeline.PointHighlightDecorator({
                date: d,
                theme: theme
            })
        ];
        this.timeline = Timeline.create(
            this.timelineContainer.el.dom, 
            bandInfos, 
            Timeline.HORIZONTAL
        );
        // since the bands are linked we need to listen to one band only
        this._silent = true;
        this.timeline.getBand(0).addOnScrollListener(
            this.setPlaybackCenter.createDelegate(this)
        );
        
    },

    /** private: method[setPlaybackCenter]
     *  :arg band:  ``Object``
     *
     *  When the timeline is moved, update the playback tool.
     */
    setPlaybackCenter: function(band) {
        var time = band.getCenterVisibleDate();
        if (this._silent !== true && this.playbackTool && this.playbackTool.playbackToolbar.playing !== true) {
            this._ignoreTimeChange = true;
            this.playbackTool.setTime(time);
            this.timeline.getBand(0)._decorators[0]._date = time;
            this.timeline.getBand(0)._decorators[0].paint();
            delete this._ignoreTimeChange;
            this.showAnnotations(time);
        }
    },
    
    /** private: method[bindViewer]
     *  :arg viewer: ``gxp.Viewer``
     *
     *  Bind the timeline with the viewer, so we get updates on layer changes.
     */
    bindViewer: function(viewer) {
        if (this.viewer) {
            this.unbindViewer();
        }
        this.viewer = viewer;
        if (!this.layerLookup) {
            this.layerLookup = {};
        }
        var layerStore = viewer.mapPanel.layers;
        if (layerStore.getCount() > 0) {
            this.onLayerStoreAdd(layerStore, layerStore.getRange());
        }
        layerStore.on({
            add: this.onLayerStoreAdd,
            remove: this.onLayerStoreRemove,
            scope: this
        });
        viewer.mapPanel.map.events.on({
            moveend: this.onMapMoveEnd,
            scope: this
        });
    },
    
    /** private: method[unbindViewer]
     *
     *  Unbind this timeline from the current viewer.
     */
    unbindViewer: function() {
        var mapPanel = this.viewer && this.viewer.mapPanel;
        if (mapPanel) {
            mapPanel.layers.unregister("add", this.onLayerStoreAdd, this);
            mapPanel.layers.unregister("remove", this.onLayerStoreRemove, this);
            mapPanel.map.un({
                moveend: this.onMapMoveEnd,
                scope: this
            });
        }
        delete this.viewer;
        delete this.layerLookup;
        delete this.schemaCache;
        delete this.propertyNamesCache;
    },

    /** private: method[getKey]
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :returns:  ``String``
     *
     *  Get a unique key for the layer record.
     */
    getKey: function(record) {
        return record.get("source") + "/" + record.get("name");
    },

    /** private: method[getTimeAttribute]
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg protocol: ``OpenLayers.Protocol``
     *  :arg schema: ``GeoExt.data.AttributeStore``
     *  :arg callback: ``Function``
     *
     *  Get the time attribute through the time info endpoint.
     *  Currently this is a MapStory specific protocol.
     */
    getTimeAttribute: function(record, protocol, schema, callback) {
        var key = this.getKey(record);
        Ext.Ajax.request({
            method: "GET",
            url: this.timeInfoEndpoint,
            params: {layer: record.get('name')},
            success: function(response) {
                var result = Ext.decode(response.responseText);
                if (result) {
                    callback.call(this, result, key, record, protocol, schema);
                }
            },
            scope: this
        });
    },

    /** private: method[onLayerStoreRemove]
     *  :arg store: ``GeoExt.data.LayerStore``
     *  :arg record: ``Ext.data.Record``
     *  :arg index: ``Integer``
     *
     *  Handler for when layers get removed from the map. 
     */
    onLayerStoreRemove: function(store, record, index) {
        var key = this.getKey(record);
        if (this.layerLookup[key]) {
            var layer = this.layerLookup[key].layer;
            if (layer) {
                this.clearEventsForKey(key);
                layer.events.un({
                    loadstart: this.onLoadStart,
                    loadend: this.onLoadEnd,
                    featuresremoved: this.onFeaturesRemoved,
                    scope: this
                });
                delete this.schemaCache[key];
                delete this.propertyNamesCache[key];
                delete this.layerLookup[key];
                layer.destroy();
            }
        }
    },

    /** private: method[parseSLD]
     *  :arg response: ``Object``
     *  :arg key: ``String``
     *  :arg callback: ``Function``
     *
     *  Parse the SLD using an OpenLayers parser and store it in the cache.
     */
    parseSLD: function(response, key, callback) {
        var parser = new OpenLayers.Format.SLD();
        this.sldCache[key] = parser.read(response.responseXML || response.responseText);
        callback && callback.call(this);
    },

    /** private: method[getFilterFromSLD]
     *  :arg key: ``String``
     *  :arg styleName: ``String``
     *  :returns: ``OpenLayers.Filter``
     *
     *  Extract the Filter from the SLD.
     */
    getFilterFromSLD: function(key, styleName) {
        var sld = this.sldCache[key];
        if (sld === undefined) {
            return false;
        }
        var filters = [];
        var elseFilter = false;
        for (var lyr in sld.namedLayers) {
            for (var i=0, ii=sld.namedLayers[lyr].userStyles.length; i<ii; ++i) {
                var style = sld.namedLayers[lyr].userStyles[i];
                if ((styleName === "" && style.isDefault === true) || (style.name === styleName)) {
                    for (var j=0, jj=style.rules.length; j<jj; ++j) {
                        var rule = style.rules[j];
                        if (rule.elseFilter === true) {
                            elseFilter = true;
                            break;
                        } else if (rule.filter) {
                            filters.push(rule.filter);
                        }
                    }
                        
                }
            }
        }
        if (elseFilter === true) {
            return false;
        }
        else if (filters.length === 1) {
            return filters[0];
        }
        else if (filters.length > 0) {
            return new OpenLayers.Filter.Logical({
                type: OpenLayers.Filter.Logical.OR,
                filters: filters
            });
        } else {
            return false;
        }
    },

    /** private: method[getSLD]
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg callback: ``Function``
     *
     *  Retrieve the SLD through a GetStyles request.
     */
    getSLD: function(record, callback) {
        var key = this.getKey(record);
        var layer = record.getLayer();
        Ext.Ajax.request({
            url: layer.url,
            params: {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetStyles",
                "LAYERS": [layer.params["LAYERS"]].join(",")
            },
            method: "GET",
            disableCaching: false,
            success: this.parseSLD.createDelegate(this, [key, callback], 1),
            scope: this
        });
    },

    /** private: method[onLayerStoreAdd]
     *  :arg store: ``GeoExt.data.LayerStore``
     *  :arg records: ``Array``
     *
     *  Handler for when new layers get added to the map. Make sure they also
     *  show up in the timeline.
     */
    onLayerStoreAdd: function(store, records) {
        var record;
        for (var i=0, ii=records.length; i<ii; ++i) {
            record = records[i];
            var layer = record.getLayer();
            if (layer.dimensions && layer.dimensions.time) {
                var source = this.viewer.getSource(record);
                if (gxp.plugins.WMSSource && (source instanceof gxp.plugins.WMSSource)) {
                    source.getWFSProtocol(record, function(protocol, schema, record) {
                        if (!protocol) {
                            // TODO: add logging to viewer
                            throw new Error("Failed to get protocol for record: " + record.get("name"));
                        }
                        var key = this.getKey(record);
                        this.schemaCache[key] = schema;
                        var callback = function(result, key, record, protocol, schema) {
                            if (result.attribute) {
                                this.layerLookup[key] = Ext.applyIf(this.layerLookup[key] || {}, {
                                    timeAttr: result.attribute,
                                    endTimeAttr: result.endAttribute,
                                    visible: false
                                });
                                this.addVectorLayer(record, protocol, schema);
                            }
                        };
                        var sldCallback;
                        if (this.layerLookup && this.layerLookup[key] && this.layerLookup[key].timeAttr) {
                            sldCallback = function() {
                                if (this.layerLookup[key].clientSideFilter) {
                                    // transform back into an OpenLayers Filter object
                                    this.layerLookup[key].clientSideFilter = new OpenLayers.Filter(this.layerLookup[key].clientSideFilter);
                                }
                                this.addVectorLayer(record, protocol, schema);
                            };
                        } else {
                            sldCallback = function() {
                                this.getTimeAttribute(record, protocol, schema, callback);
                            };
                        }
                        if (!this.sldCache[key]) {
                            this.getSLD(record, sldCallback);
                        } else {
                            sldCallback.call(this);
                        }
                    }, this);
                }
            }
        }
    },

    /** private: method[onLayout]
     *
     *  Fired by Ext, create the timeline.
     */
    onLayout: function() {
        gxp.TimelinePanel.superclass.onLayout.call(this, arguments);
        if (!this.timeline) {
            if (this.playbackTool && this.playbackTool.playbackToolbar) {
                this.setRange(this.playbackTool.playbackToolbar.control.range);
                this.setCenterDate(this.playbackTool.playbackToolbar.control.currentTime);
            }
        }
    },

    /** private: method[findBestZoomLevel]
     *  :arg range: ``Array``
     *
     *  Find the best zoom level to display the range and perform the zoom.
     */
    findBestZoomLevel: function(range) {
        if (this.timeline) {
            this._silent = true;
            var diff = range[1]-range[0];
            var band = this.timeline.getBand(0);
            var length = band.getViewLength()/2;
            if (length > 0) {
                var level = diff/band.getEther()._interval;
                var pixels = length/level;
                var delta;
                var prevDelta = Number.POSITIVE_INFINITY;
                var idx;
                for (var i=0, ii=band._zoomSteps.length; i<ii; ++i) {
                    delta = Math.abs(band._zoomSteps[i].pixelsPerInterval-pixels);
                    if (delta < prevDelta) {
                        idx = i;
                    }
                    prevDelta = delta;
                }
                if (idx !== band._zoomIndex) {
                    var zoomIn = idx < band._zoomIndex;
                    while (idx != band._zoomIndex) {
                        band.zoom(zoomIn);
                    }
                }
                this.timeline.paint();
                delete this._silent;
            }
        }
    },

    /** private: method[setRange]
     *  :arg range: ``Array``
     *
     *  Set the range for the bands of this timeline.
     */
    setRange: function(range) {
        this.originalRange = range;
        if (!this.timeline) {
            this.createTimeline(range);
        }
        // if we were not rendered, the above will not have created the timeline
        if (this.timeline) {
            var firstBand = this.timeline.getBand(0);
            firstBand.setMinVisibleDate(range[0]);
            firstBand.setMaxVisibleDate(range[1]);
            var secondBand = this.timeline.getBand(1);
            secondBand.getEtherPainter().setHighlight(range[0], range[1]);
        }
    },

    /** private: method[updateRangeSlider]
     *  :arg range: ``Array``
     *
     *  Update the slider tip for the range slider.
     */
    updateRangeSlider: function(range) {
        this.rangeSlider.startDate = range[0].dateFormat('Y-m-d');
        this.rangeSlider.endDate = range[1].dateFormat('Y-m-d');
    },

    /** private: method[displayTooltip]
     *  :arg record: ``GeoExt.data.FeatureRecord``
     *
     *  Create and show the tooltip for a record.
     */
    displayTooltip: function(record) {
        var hasGeometry = (record.getFeature().geometry !== null);
        if (!this.tooltips) {
            this.tooltips = {};
        }
        var fid = record.getFeature().fid;
        if (!this.tooltips[fid]) {
            if (!hasGeometry) {
                this.tooltips[fid] = new Ext.Tip({
                    cls: 'gxp-annotations-tip',
                    html: '<h4>' + record.get("title") + '</h4>' + record.get('content')
                });
            } else {
                this.tooltips[fid] = new GeoExt.FeatureTip({
                    map: this.viewer.mapPanel.map,
                    location: record.getFeature(),
                    cls: 'gxp-annotations-tip',
                    html: '<h4>' + record.get("title") + '</h4>' + record.get('content')
                });
            }
        }
        var tooltip = this.tooltips[fid];
        if (!hasGeometry) {
            // http://www.sencha.com/forum/showthread.php?101593-OPEN-1054-Tooltip-anchoring-problem
            tooltip.showBy(this.viewer.mapPanel.body, record.get("appearance"), [10, 10]);
            tooltip.showBy(this.viewer.mapPanel.body, record.get("appearance"), [10, 10]);
        } else {
            tooltip.show();
        }
    },

    /** private: method[hideTooltip]
     *  :arg record: ``GeoExt.data.FeatureRecord``
     *
     *  Hide the tooltip associated with the record.
     */
    hideTooltip: function(record) {
        var fid = record.getFeature().fid;
        if (this.tooltips && this.tooltips[fid]) {
            this.tooltips[fid].hide();
        }
    },

    /** private: method[showAnnotations]
     *  :arg time: ``Date``
     *
     *  Show annotations in the map.
     */
    showAnnotations: function(time) {
        if (!this.annotationsLayer) {
            this.annotationsLayer = new OpenLayers.Layer.Vector(null, {
                displayInLayerSwitcher: false,
                styleMap: new OpenLayers.StyleMap({'default':{
                    label: "${title}\n${content}",
                    fontColor: "black",
                    fontSize: "12px",
                    fontFamily: "Courier New, monospace",
                    fontWeight: "bold",
                    labelOutlineColor: "white",
                    labelAlign: "middle",
                    labelOutlineWidth: 3
                }})
            });
            this.viewer && this.viewer.mapPanel.map.addLayer(this.annotationsLayer);
        }
        var compare = time.getTime()/1000;
        if (this.featureManager && this.featureManager.featureStore) {
            this.featureManager.featureStore.each(function(record) {
                var mapFilterAttr = this.annotationConfig.mapFilterAttr;
                if (Ext.isBoolean(record.get(mapFilterAttr)) ? record.get(mapFilterAttr) : (record.get(mapFilterAttr) === "true")) {
                    var startTime = parseFloat(record.get(this.annotationConfig.timeAttr));
                    var endTime = record.get(this.annotationConfig.endTimeAttr);
                    var ranged = (endTime != startTime);
                    if (endTime == "" || endTime == null) {
                        endTime = this.playbackTool.playbackToolbar.control.range[1].getTime();
                    }
                    if (ranged === true) {
                        if (compare <= parseFloat(endTime) && compare >= startTime) {
                            this.displayTooltip(record);
                        } else {
                            this.hideTooltip(record);
                        }
                    } else {
                        var diff = Math.abs(Math.abs(startTime)-Math.abs(compare));
                        var percentage = diff/Math.abs(startTime)*100;
                        // we need to take a margin for the feature to have a chance to show up
                        if (percentage <= 2.5) {
                            this.displayTooltip(record);
                        } else {
                            this.hideTooltip(record);
                        }
                    }
                }
            }, this);
        }
    },

    /** private: method[setCenterDate]
     *  :arg time: ``Date``
     *      
     *  Set the center datetime on the bands of this timeline.
     */
    setCenterDate: function(time) {
        if (this.timeline) {
            this.timeline.getBand(0)._decorators[0]._date = time;
            this.timeline.getBand(0)._decorators[0].paint();
            this.timeline.getBand(0).setCenterVisibleDate(time);
            if (this.rangeInfo && this.rangeInfo.current) {
                var currentRange = this.rangeInfo.current;
                var originalRange = this.rangeInfo.original;
                // update once the time gets out of the original range
                if (time < originalRange[0] || time > originalRange[1]) {
                    var span = currentRange[1] - currentRange[0];
                    var start = new Date(time.getTime() - span/2);
                    var end = new Date(time.getTime() + span/2);
                    // don't go beyond the original range
                    start = new Date(Math.max(this.originalRange[0], start));
                    end = new Date(Math.min(this.originalRange[1], end));
                    this.rangeInfo.current = [start, end];
                    // calculate back the original extent
                    var startOriginal = new Date(time.getTime() - span/4);
                    var endOriginal = new Date(time.getTime() + span/4);
                    this.rangeInfo.original = [startOriginal, endOriginal];
                    // we have moved ahead in time, and we have not moved so far that 
                    // all our data is invalid
                    if (start > currentRange[0] && start < currentRange[1]) {
                        // only request the slice of data that we need
                        start = currentRange[1];
                    }
                    // we have moved back in time
                    if (start < currentRange[0] && end > currentRange[0]) {
                        end = currentRange[0];
                    }
                    for (var key in this.layerLookup) {
                        var layer = this.layerLookup[key].layer;
                        layer && this.setTimeFilter(key, this.createTimeFilter([start, end], key, 0, false));
                    }
                    // do not abort previous requests, since this will lead to blanks in the timeline
                    this.updateTimelineEvents({force: true, noAbort: true}, true);
                }
            }
        }
        this.showAnnotations(time);
    },

    /** private: method[calculateNewRange]
     *  :arg range: ``Array``
     *  :arg percentage: ``Float``
     *  :returns: ``Array``
     *      
     *  Extend the range with a certain percentage. This changes both sides
     *  of the range.
     */
    calculateNewRange: function(range, percentage) {
        if (this.playbackTool) {
            if (percentage === undefined) {
                percentage = this.rangeSlider.getValue();
            }
            var span = range[1] - range[0];
            var center = this.playbackTool.playbackToolbar.control.currentTime;
            var newSpan = (percentage/100)*span;
            var start = new Date(center.getTime() - newSpan/2);
            var end = new Date(center.getTime() + newSpan/2);
            return [start, end];
        }
    },

    /** private: method[createTimeFilter]
     *  :arg range: ``Array``
     *  :arg key: ``String``
     *  :arg fraction: ``Float``
     *  :arg updateRangeInfo: ``Boolean`` Should we update this.rangeInfo?
     *  :returns: ``OpenLayers.Filter``
     *      
     *  Create an OpenLayers.Filter to use in the WFS requests.
     */
    createTimeFilter: function(range, key, fraction, updateRangeInfo) {
        var start = new Date(range[0].getTime() - fraction * (range[1] - range[0]));
        var end = new Date(range[1].getTime() + fraction * (range[1] - range[0]));
        // don't go beyond the original range
        if(this.originalRange){
            start = new Date(Math.max(this.originalRange[0], start));
            end = new Date(Math.min(this.originalRange[1], end));
        }
        if (updateRangeInfo !== false) {
            this.rangeInfo = {
                original: range,
                current: [start, end]
            };
        }
        // do not use start and end, since this might only be a portion of the range
        // when the timeline moves, it does this intelligently as to only fetch the
        // necessary new slice of data, which is represented by start and end.
        this.updateRangeSlider(this.rangeInfo.current);
        if (this.playbackTool && this.playbackTool.playbackToolbar.playing !== true) {
            // remember this takes a lot of resources from the browser, so don't do this
            // when in playback mode
            this.findBestZoomLevel([start, end]);
        }
        if (this.layerLookup[key].endTimeAttr) {
            return new OpenLayers.Filter({
                type: OpenLayers.Filter.Logical.OR,
                filters: [
                    new OpenLayers.Filter({
                        type: OpenLayers.Filter.Comparison.BETWEEN,
                        property: this.layerLookup[key].timeAttr,
                        lowerBoundary: OpenLayers.Date.toISOString(start),
                        upperBoundary: OpenLayers.Date.toISOString(end)
                    }),
                    new OpenLayers.Filter({
                        type: OpenLayers.Filter.Comparison.BETWEEN,
                        property: this.layerLookup[key].endTimeAttr,
                        lowerBoundary: OpenLayers.Date.toISOString(start),
                        upperBoundary: OpenLayers.Date.toISOString(end)
                    })
                ]
            });
        } else {
            return new OpenLayers.Filter({
                type: OpenLayers.Filter.Comparison.BETWEEN,
                property: this.layerLookup[key].timeAttr,
                lowerBoundary: OpenLayers.Date.toISOString(start),
                upperBoundary: OpenLayers.Date.toISOString(end)
            });
        }
    },

    /** private: method[onLoadStart]
     *
     *  When a WFS layer loads for the timeline, show a busy mask.
     */ 
    onLoadStart: function() {
        this.layerCount++;
        if (!this.busyMask) {
            this.busyMask = new Ext.LoadMask(this.bwrap, {msg: this.loadingMessage});
        }
        this.busyMask.show();
    },

    /** private: method[onLoadEnd]
     *
     *  When all WFS layers are ready, hide the busy mask.
     */
    onLoadEnd: function() {
        this.layerCount--;
        if(this.layerCount === 0) {
            this.busyMask.hide();
        }
    },

    /** private: method[createHitCountProtocol]
     *  :arg protocolOptions: ``Object``
     *  :returns: ``OpenLayers.Protocol.WFS``
     *
     *  Create a hitCount protocol based on the main WFS protocol. This will
     *  be used to see if we will get too many features to show in the timeline.
     */
    createHitCountProtocol: function(protocolOptions) {
        return new OpenLayers.Protocol.WFS(Ext.apply({
            version: "1.1.0",
            readOptions: {output: "object"},
            resultType: "hits"
        }, protocolOptions));
    },

    /** private: method[assembleFullFilter]
     *  :arg key: ``String``
     *  :returns: ``OpenLayers.Filter``
     *
     *  Combine the time filter and filter extracted from the SLD into one
     *  full filter.
     */
    assembleFullFilter: function(key) {
        var lookup = this.layerLookup[key];
        var filters = [];
        if (lookup.sldFilter !== false) {
            filters.push(lookup.sldFilter);
        }
        if (lookup.timeFilter) {
            filters.push(lookup.timeFilter);
        }
        if (lookup.clientSideFilter) {
            filters.push(lookup.clientSideFilter);
        }
        var filter = null;
        if (filters.length === 1) {
            filter = filters[0];
        } else if (filters.length > 1) {
            filter = new OpenLayers.Filter.Logical({
                type: OpenLayers.Filter.Logical.AND,
                filters: filters
            });
        }
        return filter;
    },

    /** private: method[setTimeFilter]
     *  :arg key: ``String``
     *  :arg filter: ``OpenLayers.Filter``
     *
     *  Set the time filter on the layer as a property. This will be used by the
     *  protocol when retrieving data.
     */
    setTimeFilter: function(key, filter) {
        this.layerLookup[key].timeFilter = filter;
        if (this.layerLookup[key].layer) {
            this.layerLookup[key].layer.filter = this.assembleFullFilter(key);
        }
    },
    
    /** private: method[addVectorLayer]
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg protocol: ``OpenLayers.Protocol``
     *  :arg schema: ``GeoExt.data.AttributeStore``
     *
     *  Create an internal vector layer which will retrieve the events for
     *  the timeline, using WFS and a BBOX strategy.
     */
    addVectorLayer: function(record, protocol, schema) {
        var key = this.getKey(record);
        var style = record.getLayer().params.STYLES;
        this.layerLookup[key].sldFilter = this.getFilterFromSLD(key, style);
        if (this.playbackTool) {
            // TODO consider putting an api method getRange on playback tool
            var range = this.playbackTool.playbackToolbar.control.range;
            range = this.calculateNewRange(range);
            this.setCenterDate(this.playbackTool.playbackToolbar.control.currentTime);
            // create a PropertyIsBetween filter
            this.setTimeFilter(key, this.createTimeFilter(range, key, this.bufferFraction));
        }
        var filter = this.assembleFullFilter(key);
        var layer = new OpenLayers.Layer.Vector(key, {
            strategies: [new OpenLayers.Strategy.BBOX({
                ratio: 1.1,
                resFactor: 1,
                autoActivate: false
            })],
            filter: filter,
            protocol: protocol,
            displayInLayerSwitcher: false,
            visibility: false
        });
        layer.events.on({
            /*loadstart: this.onLoadStart,
            loadend: this.onLoadEnd,*/
            featuresadded: this.onFeaturesAdded.createDelegate(this, [key], 1),
            featuresremoved: this.onFeaturesRemoved,
            scope: this
        });

        var titleAttr = this.guessTitleAttribute(schema);
        Ext.applyIf(this.layerLookup[key], {
            layer: layer,
            titleAttr: titleAttr,
            hitCount: this.createHitCountProtocol(protocol.options)
        });
        this.viewer.mapPanel.map.addLayer(layer);
    },

    /** private: method[onMapMoveEnd]
     *  Registered as a listener for map moveend.
     */
    onMapMoveEnd: function() {
        this._silentMapMove !== true && this.updateTimelineEvents();
        this.filterAnnotationsByBBOX();
    },

    /** private: method[filterAnnotationsByBBOX]
     *  Makee sure only annotations show up that are in the map.
     */
    filterAnnotationsByBBOX: function() {
        if (this.featureManager && this.featureManager.featureStore) {
            var fids = [];
            this.featureManager.featureStore.each(function(record) {
                var feature = record.getFeature();
                if (feature.geometry !== null) {
                    var bounds = feature.geometry.getBounds();
                    if (!bounds.intersectsBounds(this.viewer.mapPanel.map.getExtent())) {
                        fids.push(feature.fid);
                    }
                }
            }, this);
            var filterMatcher = function(evt) {
                return (fids.indexOf(evt.getProperty('fid')) === -1);
            };
            this.setFilterMatcher(filterMatcher);
        }
    },
    
    /** private: method[updateTimelineEvents]
     *  :arg options: `Object` First arg to OpenLayers.Strategy.BBOX::update.
     *  :arg clearWhenInvisible: ``Boolean`` If true, only clear if events are
     *  outside of the visible band.
     *
     *  Load the data for the timeline. Only load the data if the total number
     *  features is below a configurable threshold.
     */
    updateTimelineEvents: function(options, clearWhenInvisible) {
        if (!this.rendered) {
            return;
        }
        var dispatchQueue = [];
        var layer, key;
        for (key in this.layerLookup) {
            layer = this.layerLookup[key].layer;
            if (this.layerLookup[key].visible && layer && layer.strategies !== null) {
                var protocol = this.layerLookup[key].hitCount;

                // a real solution would be something like:
                // http://trac.osgeo.org/openlayers/ticket/3569
                var bounds = layer.strategies[0].bounds;
                layer.strategies[0].calculateBounds();
                var filter = new OpenLayers.Filter.Spatial({
                    type: OpenLayers.Filter.Spatial.BBOX,
                    value: layer.strategies[0].bounds,
                    projection: layer.projection
                });
                layer.strategies[0].bounds = bounds;
            
                if (layer.filter) {
                    filter = new OpenLayers.Filter.Logical({
                        type: OpenLayers.Filter.Logical.AND,
                        filters: [layer.filter, filter]
                    });
                }
                // end of TODO
                protocol.filter = protocol.options.filter = filter;
                var func = function(done, storage) {
                    this.read({
                        callback: function(response) {
                            if (storage.numberOfFeatures === undefined) {
                                storage.numberOfFeatures = 0;
                            }
                            storage.numberOfFeatures += response.numberOfFeatures;
                            done();
                        }
                    });
                };
                dispatchQueue.push(func.createDelegate(protocol));
            }
        }
        gxp.util.dispatch(dispatchQueue, function(storage) {
            if (storage.numberOfFeatures <= this.maxFeatures) {
                this.timelineContainer.el.unmask(true);
                for (key in this.layerLookup) {
                    layer = this.layerLookup[key].layer;
                    if (layer && layer.strategies !== null) {
                        if (clearWhenInvisible === true) {
                            this.clearInvisibleEvents(key);
                        } else {
                            this.clearEventsForKey(key);
                        }
                        var schema = this.schemaCache[key];
                        var propertyNames = this.propertyNamesCache[key];
                        if (!propertyNames) {
                            propertyNames = [];
                            schema.each(function(r) {
                                var name = r.get("name");
                                var type = r.get("type");
                                if (!type.match(/^[^:]*:?((Multi)?(Point|Line|Polygon|Curve|Surface|Geometry))/)) {
                                    propertyNames.push(name);
                                }
                            });
                            this.propertyNamesCache[key] = propertyNames;
                        }
                        options = options || {};
                        options.propertyNames = propertyNames;
                        layer.strategies[0].activate();
                        layer.strategies[0].update(options);
                    }
                }
            } else {
                // clear the timeline and show instruction text
                for (key in this.layerLookup) {
                    layer = this.layerLookup[key].layer;
                    if (layer && layer.strategies !== null) {
                        layer.strategies[0].deactivate();
                    }
                }
                var msg;
                if (isNaN(storage.numberOfFeatures)) {
                    msg = this.errorText;
                } else {
                    var tpl = new Ext.Template(this.instructionText);
                    msg = tpl.applyTemplate({count: storage.numberOfFeatures, max: this.maxFeatures});
                }
                this.timelineContainer.el.mask(msg, '');
                this.eventSource.clear();
            }
        }, this);
    },

    /** private: method[clearEventsForKey]
     *  :arg key: ``String`` 
     *
     *  Clear the events from the timeline for a certain layer.
     */
    clearEventsForKey: function(key) {
        var iterator = this.eventSource.getAllEventIterator();
        var eventIds = [];
        while (iterator.hasNext()) {
            var evt = iterator.next();
            if (evt.getProperty('key') === key) {
                eventIds.push(evt.getID());
            }
        }
        for (var i=0, len=eventIds.length; i<len; ++i) {
            this.eventSource.remove(eventIds[i]);
        }
        this.timeline && this.timeline.layout();
    },

    /** private: method[clearInvisibleEvents]
     *  :arg key: ``String`` 
     *
     *  Clear the events from the timeline for a certain layer but only clear
     *  the events that are outside of the visible range.
     */
    clearInvisibleEvents: function(key) {
        if (this.timeline) {
            var band = this.timeline.getBand(0);
            var min = band.getMinVisibleDate();
            var max = band.getMaxVisibleDate();
            var iterator = this.eventSource.getAllEventIterator();
            var eventIds = [];
            while (iterator.hasNext()) {
                var evt = iterator.next();
                var start = evt.getProperty('start');
                var visible = start >= min && start <= max;
                if (evt.getProperty('key') === key && !visible) {
                    eventIds.push(evt.getID());
                }
            }
            for (var i=0, len=eventIds.length; i<len; ++i) {
                this.eventSource.remove(eventIds[i]);
            }
            this.timeline.layout();
        }
    },

    /** private: method[clearEventsForRange]
     *  :arg key: ``String`` 
     *  :arg range: ``Array``
     *
     *  Clear the events from the timeline for a certain layer for dates that
     *  are within the supplied range.
     */
    clearEventsForRange: function(key, range) {
        var iterator = this.eventSource.getAllEventIterator();
        var eventIds = [];
        while (iterator.hasNext()) {
            var evt = iterator.next();
            var start = evt.getProperty('start');
            // only clear if in range
            if (evt.getProperty('key') === key && start >= range[0] && start <= range[1]) {
                eventIds.push(evt.getID());
            }
        }
        for (var i=0, len=eventIds.length; i<len; ++i) {
            this.eventSource.remove(eventIds[i]);
        }
        this.timeline && this.timeline.layout();
    },

    /** private: method[clearEventsForFid]
     *  :arg key: ``String``
     *  :arg fid:  ``String``
     *
     *  Clear the events from the timeline for a certain feature.
     */
    clearEventsForFid: function(key, fid) {
        var iterator = this.eventSource.getAllEventIterator();
        var eventIds = [];
        while (iterator.hasNext()) {
            var evt = iterator.next();
            if (evt.getProperty('key') === key && evt.getProperty('fid') === fid) {
                eventIds.push(evt.getID());
            }
        }   
        for (var i=0, len=eventIds.length; i<len; ++i) {
            this.eventSource.remove(eventIds[i]);
        }
        this.timeline && this.timeline.layout();
    },

    /** private: method[onFeaturesRemoved]
     *  :arg event: ``Object`` 
     *
     *  Memory management for when features get removed.
     */
    onFeaturesRemoved: function(event) {
        // clean up
        for (var i=0, len=event.features.length; i<len; i++) {
            event.features[i].destroy();
        }
    },

    /** private: method[addFeatures]
     *  :arg key: ``String``
     *  :arg features: ``Array``
     *
     *  Add some features to the timeline.
     */    
    addFeatures: function(key, features) {
        var isDuration = false;
        var titleAttr = this.layerLookup[key].titleAttr;
        var timeAttr = this.layerLookup[key].timeAttr;
        var endTimeAttr = this.layerLookup[key].endTimeAttr;
        var filterAttr = this.layerLookup[key].filterAttr;
        if (endTimeAttr) {
            isDuration = true;
        }
        var num = features.length;
        var events = [];
        var attributes, str;
        for (var i=0; i<num; ++i) { 
            attributes = features[i].attributes;
            if (isDuration === false) {
                events.push({
                    start: OpenLayers.Date.parse(attributes[timeAttr]),
                    title: attributes[titleAttr],
                    durationEvent: false,
                    key: key,
                    icon: this.layerLookup[key].icon,
                    fid: features[i].fid
                });
            } else if (Ext.isBoolean(attributes[filterAttr]) ? attributes[filterAttr] : (attributes[filterAttr] === "true")) {
                var start = attributes[timeAttr];
                var end = attributes[endTimeAttr];
                // end is optional
                var durationEvent = (start != end);
                if (!Ext.isEmpty(start)) {
                    start = parseFloat(start);
                    if (Ext.isNumber(start)) {
                        start = new Date(start*1000);
                    } else {
                        start = OpenLayers.Date.parse(start);
                    }
                }
                if (!Ext.isEmpty(end)) {
                    end = parseFloat(end);
                    if (Ext.isNumber(end)) {
                        end = new Date(end*1000);
                    } else {
                        end = OpenLayers.Date.parse(end);
                    }
                }
                if (durationEvent === false) {
                    end = undefined;
                } else {
                    if (end == "" || end == null) {
                        // Simile does not deal with unlimited ranges, so let's
                        // take the range from the playback control
                        end = this.playbackTool.playbackToolbar.control.range[1];
                    }
                }
                events.push({
                    start: start,
                    end: end,
                    icon: this.layerLookup[key].icon,
                    title: attributes[titleAttr],
                    durationEvent: durationEvent,
                    key: key,
                    fid: features[i].fid
                });
            }
        }       
        var feed = {
            dateTimeFormat: "javascriptnative", //"iso8601",
            events: events
        };
        // do not use a real URL here, since this will mess up relative URLs
        this.eventSource.loadJSON(feed, "mapstory.org");
    },

    /** private: method[onFeaturesAdded]
     *  :arg event: ``Object``
     *  :arg key: ``String``
     *
     *  When features get added to the vector layer, add them to the timeline.
     */
    onFeaturesAdded: function(event, key) {
        var features = event.features;
        this.addFeatures(key, features);
    },

    /** private: method[onResize]
     *  Private method called after the panel has been resized.
     */
    onResize: function() {
        gxp.TimelinePanel.superclass.onResize.apply(this, arguments);
        this.timeline && this.timeline.layout();
    },

    /** private: method[beforeDestroy]
     *  Cleanup.
     */
    beforeDestroy : function(){
        gxp.TimelinePanel.superclass.beforeDestroy.call(this);
        for (var key in this.layerLookup) {
            var layer = this.layerLookup[key].layer;
            if (layer) {
                layer.events.un({
                    loadstart: this.onLoadStart,
                    loadend: this.onLoadEnd,
                    featuresremoved: this.onFeaturesRemoved,
                    scope: this
                });
                layer.destroy();
            }
        }
        this.annotationsRecord = null;
        this.annotationsLayer = null;
        this.destroyPopup();
        this.unbindViewer();
        this.unbindFeatureEditor();
        this.unbindPlaybackTool();
        if (this.rendered){
            Ext.destroy(this.busyMask);
        }
        this.eventSource = null;
        if (this.timeline) {
            this.timeline.dispose();
            this.timeline = null;
        }
        this.busyMask = null;
    },

    /** api: method[getState]
     *  :returns {Object} - user configured settings
     *  
     *  Widget specific implementation of the getState function
     */
    getState: function() {
        var result = {
            layerLookup: {}
        };
        for (var key in this.layerLookup) {
            var info = this.layerLookup[key];
            result.layerLookup[key] = {
                titleAttr: info.titleAttr,
                timeAttr: info.timeAttr,
                endTimeAttr: info.endTimeAttr,
                visible: info.visible,
                clientSideFilter: info.clientSideFilter
            };
        }
        return result;
    }

});

/** api: xtype = gxp_timelinepanel */
Ext.reg("gxp_timelinepanel", gxp.TimelinePanel);
