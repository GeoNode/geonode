/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

//TODO remove the WMSStylesDialog and GeoServerStyleWriter includes
/**
 * @include widgets/WMSStylesDialog.js
 * @include plugins/GeoServerStyleWriter.js
 * @include GeoExt/widgets/LayerOpacitySlider.js
 * @require OpenLayers/Format/CQL.js
 * @require widgets/FilterBuilder.js
 */

/** api: (define)
 *  module = gxp
 *  class = WMSLayerPanel
 *  base_link = `Ext.TabPanel <http://extjs.com/deploy/dev/docs/?class=Ext.TabPanel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: WMSLayerPanel(config)
 *
 *      Create a dialog for setting WMS layer properties like title, abstract,
 *      opacity, transparency and image format.
 */
gxp.HHLayerPanel = Ext.extend(Ext.TabPanel, {

    /** api: config[layerRecord]
     *  ``GeoExt.data.LayerRecord``
     *  Show properties for this layer record.
     */
    layerRecord: null,

    /** api: config[source]
     *  ``gxp.plugins.LayerSource``
     *  Source for the layer. Optional. If not provided, ``sameOriginStyling``
     *  will be ignored.
     */
    source: null,

    /** private: property[transparent]
     *  ``Boolean``
     *  Used to store the previous state of the transparent checkbox before
     *  changing the image format to jpeg (and automagically changing
     *  the checkbox to disabled and unchecked).
     */
    transparent: null,

    /** api: config[activeTab]
     *  ``String or Number``
     *  A string id or the numeric index of the tab that should be initially
     *  activated on render.  Defaults to ``0``.
     */
    activeTab: 0,

    /** api: config[border]
     *  ``Boolean``
     *  Display a border around the panel.  Defaults to ``false``.
     */
    border: false,

    /** api: config[imageFormats]
     *  ``RegEx`` Regular expression used to test browser friendly formats for
     *  GetMap requests.  The formats displayed will those from the record that
     *  match this expression.  Default is ``/png|gif|jpe?g/i``.
     */
    imageFormats: /png|gif|jpe?g/i,

    /** i18n */
    aboutText: "About",
    titleText: "Title",
    nameText: "Name",
    descriptionText: "Description",
    displayText: "Display",
    opacityText: "Opacity",
    formatText: "Tile format",
    infoFormatText: "Info format",
    infoFormatEmptyText: "Select a format",
    transparentText: "Transparent",
    displayOptionsText: "Display options",
    scaleText: "Limit by scale",
    minScaleText: "Min scale",
    maxScaleText: "Max scale",

    initComponent: function() {
        this.addEvents(
            /** api: event[change]
             *  Fires when the ``layerRecord`` is changed using this dialog.
             */
            "change"
        );
        this.items = [
            this.createAboutPanel(),
            this.createDisplayPanel()
        ];

        gxp.HHLayerPanel.superclass.initComponent.call(this);
    },


    /** private: method[createAboutPanel]
     *  Creates the about panel.
     */
    createAboutPanel: function() {
        return {
            title: this.aboutText,
            bodyStyle: {"padding": "10px"},
            defaults: {
                border: false
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
                }]
            }, {
                layout: "form",
                labelAlign: "top",
                items: [{
                    xtype: "textarea",
                    fieldLabel: this.descriptionText,
                    grow: true,
                    growMax: 150,
                    anchor: "99%",
                    value: this.layerRecord.get("abstract"),
                    readOnly: true
                }]
            }]
        };
    },

    /** private: method[onFormatChange]
     *  Handler for when the image format is changed.
     */
    onFormatChange: function(combo) {
        var layer = this.layerRecord.getLayer();
        var format = combo.getValue();
        layer.mergeNewParams({
            format: format
        });
        var cb = this.transparentCb;
        if (format == "image/jpeg") {
            this.transparent = cb.getValue();
            cb.setValue(false);
        } else if (this.transparent !== null) {
            cb.setValue(this.transparent);
            this.transparent = null;
        }
        cb.setDisabled(format == "image/jpeg");
        this.fireEvent("change");
    },

    /** private: method[addScaleOptions]
     *  :arg layer: ``OpenLayers.Layer.WMS``
     *  :arg options: ``Object``
     *
     *  Apply the scale options to the layer and redraw.
     */
    addScaleOptions: function(layer, options) {
        // work around for https://github.com/openlayers/openlayers/issues/407
        layer.alwaysInRange = null;
        layer.addOptions(options);
        layer.display();
        layer.redraw();
    },

    /** private: method[createDisplayPanel]
     *  Creates the display panel.
     */
    createDisplayPanel: function() {
        var record = this.layerRecord;
        var layer = record.getLayer();
        var opacity = layer.opacity;
        if(opacity == null) {
            opacity = 1;
        }
        // WMS parameters, we should avoid them (formats, transparent etc)
        var formats = [];
        layer.params["FORMAT"] = "image/png";
        var currentFormat = layer.params["FORMAT"].toLowerCase();
        Ext.each(record.get("formats"), function(format) {
            if(this.imageFormats.test(format)) {
                formats.push(format.toLowerCase());
            }
        }, this);
        if(formats.indexOf(currentFormat) === -1) {
            formats.push(currentFormat);
        }
        var transparent = layer.params["TRANSPARENT"];
        transparent = (transparent === "true" || transparent === true);

        return {
            title: this.displayText,
            layout: 'form',
            bodyStyle: {"padding": "10px"},
            defaults: {
                labelWidth: 70
            },
            items: [{
                xtype: "fieldset",
                title: this.displayOptionsText,
                items: [{
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
                }, {
                    xtype: "compositefield",
                    fieldLabel: this.formatText,
                    anchor: "99%",
                    items: [{
                        xtype: "combo",
                        width: 90,
                        listWidth: 150,
                        store: formats,
                        value: currentFormat,
                        mode: "local",
                        triggerAction: "all",
                        editable: false,
                        listeners: {
                            select: this.onFormatChange,
                            scope: this
                        }
                    }, {
                        xtype: "checkbox",
                        ref: '../../../transparentCb',
                        checked: transparent,
                        listeners: {
                            check: function(checkbox, checked) {
                                layer.mergeNewParams({
                                    transparent: checked ? "true" : "false"
                                });
                                 this.fireEvent("change");
                            },
                            scope: this
                        }
                    }, {
                        xtype: "label",
                        cls: "gxp-layerproperties-label",
                        text: this.transparentText
                    }]
                }, {
                    xtype: "compositefield",
                    anchor: "99%",
                    hidden: this.layerRecord.get("layer").params.TILED == null,
                    fieldLabel: this.cacheText,
                    items: [{
                        xtype: "checkbox",
                        checked: (this.layerRecord.get("layer").params.TILED === true),
                        listeners: {
                            check: function(checkbox, checked) {
                                var layer = this.layerRecord.get("layer");
                                layer.mergeNewParams({
                                    TILED: checked
                                });
                                this.fireEvent("change");
                            },
                            scope: this
                        }
                    }, {
                        xtype: "label",
                        cls: "gxp-layerproperties-label",
                        text: this.cacheFieldText
                    }]
                }, {
                    xtype: "combo",
                    fieldLabel: this.infoFormatText,
                    emptyText: this.infoFormatEmptyText,
                    store: record.get("infoFormats"),
                    value: record.get("infoFormat"),
                    hidden: (record.get("infoFormats") === undefined),
                    mode: 'local',
                    listWidth: 150,
                    triggerAction: "all",
                    editable: false,
                    anchor: "99%",
                    listeners: {
                        select: function(combo) {
                            var infoFormat = combo.getValue();
                            record.set("infoFormat", infoFormat);
                            this.fireEvent("change");
                        }
                    },
                    scope: this
                }, {
                    xtype: "fieldset",
                    title: this.scaleText,
                    listeners: {
                        expand: function() {
                            var layer = this.layerRecord.getLayer();
                            if (this.minScale !== undefined || this.maxScale !== undefined) {
                                this.addScaleOptions(layer, {minScale: this.maxScale, maxScale: this.minScale});
                            }
                        },
                        collapse: function() {
                            var layer = this.layerRecord.getLayer();
                            this.minScale = layer.options.maxScale;
                            this.maxScale = layer.options.minScale;
                            this.addScaleOptions(layer, {minScale: null, maxScale: null});
                        },
                        scope: this
                    },
                    checkboxToggle: true,
                    items: [{
                        xtype: "compositefield",
                        fieldLabel: this.minScaleText,
                        items: [{
                            xtype: "label",
                            text: "1:",
                            cls: "gxp-layerproperties-label"
                        }, {
                            xtype: "numberfield",
                            anchor: '99%',
                            width: '85%',
                            listeners: {
                                'change': function(field) {
                                    var options = {
                                        maxScale: parseInt(field.getValue())
                                    };
                                    var layer = this.layerRecord.getLayer();
                                    this.addScaleOptions(layer, options);
                                },
                                scope: this
                            },
                            value: this.layerRecord.getLayer().options.maxScale
                        }]
                    }, {
                        xtype: "compositefield",
                        fieldLabel: this.maxScaleText,
                        items: [{
                            xtype: "label",
                            text: "1:",
                            cls: "gxp-layerproperties-label"
                        }, {
                            xtype: "numberfield",
                            anchor: '99%',
                            width: '85%',
                            listeners: {
                                'change': function(field) {
                                    var options = {
                                        minScale: parseInt(field.getValue())
                                    };
                                    var layer = this.layerRecord.getLayer();
                                    this.addScaleOptions(layer, options);
                                },
                                scope: this
                            },
                            value: this.layerRecord.getLayer().options.minScale
                        }]
                    }]
                }]
            }]
        };
    }

});

Ext.reg('gxp_hhlayerpanel', gxp.HHLayerPanel);
