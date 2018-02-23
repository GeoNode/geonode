/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.menu
 *  class = LayerMenu
 *  base_link = `Ext.menu.Menu <http://extjs.com/deploy/dev/docs/?class=Ext.menu.Menu>`_
 */
Ext.namespace("gxp.menu");

/** api: constructor
 *  .. class:: LayerMenu(config)
 *
 *    A menu to control layer visibility.
 */   
gxp.menu.LayerMenu = Ext.extend(Ext.menu.Menu, {
    
    /** api: config[layerText]
     *  ``String``
     *  Text for added layer (i18n).
     */
    layerText: "Layer",
    
    /** api: config[layers]
     *  ``GeoExt.data.LayerStore``
     *  The store containing layer records to be viewed in this menu.
     */
    layers: null,
    
    /** private: method[initComponent]
     *  Private method called to initialize the component.
     */
    initComponent: function() {
        gxp.menu.LayerMenu.superclass.initComponent.apply(this, arguments);
        this.layers.on("add", this.onLayerAdd, this);
        this.onLayerAdd();
    },

    /** private: method[onRender]
     *  Private method called during the render sequence.
     */
    onRender : function(ct, position) {
        gxp.menu.LayerMenu.superclass.onRender.apply(this, arguments);
    },

    /** private: method[beforeDestroy]
     *  Private method called during the destroy sequence.
     */
    beforeDestroy: function() {
        if (this.layers && this.layers.on) {
            this.layers.un("add", this.onLayerAdd, this);
        }
        delete this.layers;
        gxp.menu.LayerMenu.superclass.beforeDestroy.apply(this, arguments);
    },
    
    /** private: method[onLayerAdd]
     *  Listener called when records are added to the layer store.
     */
    onLayerAdd: function() {
        this.removeAll();
        // this.getEl().addClass("gxp-layer-menu");
        // this.getEl().applyStyles({
        //     width: '',
        //     height: ''
        // });
        this.add(
            {
                iconCls: "gxp-layer-visibility",
                text: this.layerText,
                canActivate: false
            },
            "-"
        );
        this.layers.each(function(record) {
            var layer = record.getLayer();
            if(layer.displayInLayerSwitcher) {
                var item = new Ext.menu.CheckItem({
                    id: "layer_menu_" + layer.id,
                    text: record.get("title"),
                    checked: record.getLayer().getVisibility(),
                    group: record.get("group") == "background" ? "background" : null,
                    listeners: {
                        checkchange: function(item, checked) {
                            record.getLayer().setVisibility(checked);
                        }
                    }
                });
                if (this.items.getCount() > 2) {
                    this.insert(2, item);
                } else {
                    this.add(item);
                }
            }
        }, this);
        
    }
    
});

Ext.reg('gxp_layermenu', gxp.menu.LayerMenu);
