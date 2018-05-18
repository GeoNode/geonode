/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires OpenLayers/Control/ScaleLine.js
 * @requires GeoExt/data/ScaleStore.js
 */

/** api: (define)
 *  module = gxp
 *  class = ScaleOverlay
 *  base_link = `Ext.Panel <http://dev.sencha.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: ScaleOverlay(config)
 *   
 *      Create a panel for showing a ScaleLine control and a combobox for 
 *      selecting the map scale.
 */
gxp.ScaleOverlay = Ext.extend(Ext.Panel, {
    
    /** api: config[map]
     *  ``OpenLayers.Map`` or :class:`GeoExt.MapPanel`
     *  The map for which to show the scale info.
     */
    map: null,

    /** i18n */
    zoomLevelText: "Zoom level",

    /** private: method[initComponent]
     *  Initialize the component.
     */
    initComponent: function() {
        gxp.ScaleOverlay.superclass.initComponent.call(this);
        this.cls = 'map-overlay';
        if(this.map) {
            if(this.map instanceof GeoExt.MapPanel) {
                this.map = this.map.map;
            }
            this.bind(this.map);
        }
        this.on("beforedestroy", this.unbind, this);        
    },
    
    /** private: method[addToMapPanel]
     *  :param panel: :class:`GeoExt.MapPanel`
     *  
     *  Called by a MapPanel if this component is one of the items in the panel.
     */
    addToMapPanel: function(panel) {
        this.on({
            afterrender: function() {
                this.bind(panel.map);
            },
            scope: this
        });
    },
    
    /** private: method[stopMouseEvents]
     *  :param e: ``Object``
     */
    stopMouseEvents: function(e) {
        e.stopEvent();
    },
    
    /** private: method[removeFromMapPanel]
     *  :param panel: :class:`GeoExt.MapPanel`
     *  
     *  Called by a MapPanel if this component is one of the items in the panel.
     */
    removeFromMapPanel: function(panel) {
        var el = this.getEl();
        el.un("mousedown", this.stopMouseEvents, this);
        el.un("click", this.stopMouseEvents, this);
        this.unbind();
    },

    /** private: method[addScaleLine]
     *  
     *  Create the scale line control and add it to the panel.
     */
    addScaleLine: function() {
        var scaleLinePanel = new Ext.BoxComponent({
            autoEl: {
                tag: "div",
                cls: "olControlScaleLine overlay-element overlay-scaleline"
            }
        });
        this.on("afterlayout", function(){
            scaleLinePanel.getEl().dom.style.position = 'relative';
            scaleLinePanel.getEl().dom.style.display = 'inline';

            this.getEl().on("click", this.stopMouseEvents, this);
            this.getEl().on("mousedown", this.stopMouseEvents, this);
        }, this);
        scaleLinePanel.on('render', function(){
            var scaleLine = new OpenLayers.Control.ScaleLine({
                geodesic: true,
                div: scaleLinePanel.getEl().dom
            });

            this.map.addControl(scaleLine);
            scaleLine.activate();
        }, this);
        this.add(scaleLinePanel);
    },

    /** private: method[handleZoomEnd]
     *
     * Set the correct value in the scale combo box.
     */
    handleZoomEnd: function() {
        var scale = this.zoomStore.queryBy(function(record) { 
            return this.map.getZoom() == record.data.level;
        }, this);
        if (scale.length > 0) {
            scale = scale.items[0];
            this.zoomSelector.setValue("1 : " + parseInt(scale.data.scale, 10));
        } else {
            if (!this.zoomSelector.rendered) {
                return;
            }
            this.zoomSelector.clearValue();
        }
    },

    /** private: method[addScaleCombo]
     *  
     *  Create the scale combo and add it to the panel.
     */
    addScaleCombo: function() {
        this.zoomStore = new GeoExt.data.ScaleStore({
            map: this.map
        });
        this.zoomSelector = new Ext.form.ComboBox({
            emptyText: this.zoomLevelText,
            tpl: '<tpl for="."><div class="x-combo-list-item">1 : {[parseInt(values.scale)]}</div></tpl>',
            editable: false,
            triggerAction: 'all',
            mode: 'local',
            store: this.zoomStore,
            width: 110
        });
        this.zoomSelector.on({
            click: this.stopMouseEvents,
            mousedown: this.stopMouseEvents,
            select: function(combo, record, index) {
                this.map.zoomTo(record.data.level);
            },
            scope: this
        });
        this.map.events.register('zoomend', this, this.handleZoomEnd);
        var zoomSelectorWrapper = new Ext.Panel({
            items: [this.zoomSelector],
            cls: 'overlay-element overlay-scalechooser',
            border: false
        });
        this.add(zoomSelectorWrapper);
    },

    /** private: method[bind]
     *  :param map: ``OpenLayers.Map``
     */
    bind: function(map) {
        this.map = map;
        this.addScaleLine();
        this.addScaleCombo();
        this.doLayout();
    },
    
    /** private: method[unbind]
     */
    unbind: function() {
        if(this.map && this.map.events) {
            this.map.events.unregister('zoomend', this, this.handleZoomEnd);
        }
        this.zoomStore = null;
        this.zoomSelector = null;
    }

});

/** api: xtype = gxp_scaleoverlay */
Ext.reg('gxp_scaleoverlay', gxp.ScaleOverlay);
