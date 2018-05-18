/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */



/** api: (define)
 *  module = gxp
 *  class = ArcRestLayerPanel
 *  base_link = `Ext.TabPanel <http://extjs.com/deploy/dev/docs/?class=Ext.TabPanel>`_
 */
Ext.namespace("gxp");



/** api: constructor
 *  .. class:: ArcRestLayerPanel(config)
 *
 *      Create a dialog for setting ArcREST layer title 
 */
gxp.ArcRestLayerPanel = Ext.extend(Ext.TabPanel, {


    /** api: config[border]
     *  ``Boolean``
     *  Display a border around the panel.  Defaults to ``false``.
     */
    border: false,


   /** api: config[layerRecord]
     *  ``GeoExt.data.LayerRecord``
     *  Show properties for this layer record.
     */
    layerRecord: null,


    /** i18n */
    aboutText: "About",
    titleText: "Title",
    nameText: "Name",
    opacityText: "Opacity",

    activeTab: 0,

    initComponent: function() {
        this.addEvents(
            /** api: event[change]
             *  Fires when the ``layerRecord`` is changed using this dialog.
             */
            "change"
        );
        this.items = [
            this.createAboutPanel()
        ];

        gxp.ArcRestLayerPanel.superclass.initComponent.call(this);

    },

    
    /** private: method[createAboutPanel]
     *  Creates the about panel.
     */
    createAboutPanel: function() {
        return {
            title: this.aboutText,
            bodyStyle: {"padding": "10px"},
            defaults: {
                border: this.border
            },
            items: [{
                layout: "form",
                labelWidth: 70,
                items: [{
                    xtype: "textfield",
                    fieldLabel: this.titleText,
                    anchor: "99%",
                    value: this.layerRecord.get("title"),
                    listeners: {
                        change: function(field) {
                            this.layerRecord.set("title", field.getValue());
                            //TODO revisit when discussion on
                            // http://trac.geoext.org/ticket/110 is complete
                            this.layerRecord.commit();
                            this.fireEvent("change");
                        },
                        scope: this
                    }
                }, {
                    xtype: "textfield",
                    fieldLabel: this.nameText,
                    anchor: "99%",
                    value: this.layerRecord.get("name"),
                    readOnly: true
                },{
                    xtype: "gx_opacityslider",
                    name: "opacity",
                    anchor: "99%",
                    isFormField: true,
                    fieldLabel: this.opacityText,
                    listeners: {
                        change: function() {
                            this.fireEvent("change");
                        },
                        scope: this
                    },
                    layer: this.layerRecord
                }]
            }]
        };
    }

});

Ext.reg('gxp_arcrestlayerpanel', gxp.ArcRestLayerPanel);
