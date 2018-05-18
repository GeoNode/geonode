/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp
 *  class = NewSourceWindow
 *  extends = Ext.Window
 */
Ext.namespace("gxp");

/** api: constructor
 * .. class:: gxp.NewSourceWindow(config)
 *
 *     An Ext.Window with some defaults that better lend themselves toward use
 *     as a quick query to get a service URL from a user.
 */
gxp.MouseCoordinatesDialog = Ext.extend(Ext.Container, {

    /** private: method[initComponent]
     */
    initComponent: function() {
        Ext.apply(this, this.getConfig());
        gxp.MouseCoordinatesDialog.superclass.initComponent.call(this);
    },

    setCoordinates: function(coordinates){
        this.coordinatesBox.setValue(coordinates);
    },


    getConfig: function() {
        this.coordinatesBox = new Ext.form.TextField({
            value: this.coordinates,
            width: 300,
            listeners: {
                "focus": function() {
                    this.selectText();
                }
            }
        });

        var coordbox = new Ext.Container({
            layout: "column",
            defaults: {
                border: false,
                xtype: "box"
            },
            items: [
                this.coordinatesBox
            ]
        });

        return {
            border: false,
            defaults: {
                border: false,
                cls: "gxp-export-section",
                xtype: "container",
                layout: "fit"
            },
            items: [{
                items: [coordbox]
            }]
        };
    }

});

