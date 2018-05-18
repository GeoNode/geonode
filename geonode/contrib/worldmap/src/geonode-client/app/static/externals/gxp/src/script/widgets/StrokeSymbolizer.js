/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include widgets/form/ColorField.js
 */

/** api: (define)
 *  module = gxp
 *  class = StrokeSymbolizer
 *  base_link = `Ext.FormPanel <http://extjs.com/deploy/dev/docs/?class=Ext.FormPanel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: StrokeSymbolizer(config)
 *   
 *      Form for configuring a symbolizer stroke.
 */
gxp.StrokeSymbolizer = Ext.extend(Ext.FormPanel, {
    
    /* i18n */
    solidStrokeName: "solid",
    dashStrokeName: "dash",
    dotStrokeName: "dot",
    titleText: "Stroke",
    styleText: "Style",
    colorText: "Color",
    widthText: "Width",
    opacityText: "Opacity",
    /* ~i18n */
    
    /** api: config[symbolizer]
     *  ``Object``
     *  A symbolizer object that will be used to fill in form values.
     *  This object will be modified when values change.  Clone first if
     *  you do not want your symbolizer modified.
     */
    symbolizer: null,
    
    /** api: config[colorManager]
     *  ``Function``
     *  Optional color manager constructor to be used as a plugin for the color
     *  field.
     */
    colorManager: null,
    
    /** api: config[checkboxToggle]
     *  ``Boolean`` Set to false if the "Fill" fieldset should not be
     *  toggleable. Default is true.
     */
    checkboxToggle: true,
    
    /** api: config[defaultColor]
     *  ``String`` Default background color for the Color field. This
     *  color will be displayed when no strokeColor value for the symbolizer
     *  is available. Defaults to the ``strokeColor`` property of
     *  ``OpenLayers.Renderer.defaultSymbolizer``.
     */
    defaultColor: null,

    /** api: config[dashStyles]
     *  ``Array(Array)``
     *  A list of [value, name] pairs for stroke dash styles.
     *  The first item in each list is the value and the second is the
     *  display name.  Default is [["solid", "solid"], ["2 4", "dash"],
     *  ["1 4", "dot"]].
     */
    dashStyles: null,
    
    border: false,
    
    initComponent: function() {
        
        this.dashStyles = this.dashStyles || [["solid", this.solidStrokeName], ["4 4", this.dashStrokeName], ["2 4", this.dotStrokeName]];
        
        if(!this.symbolizer) {
            this.symbolizer = {};
        }
        
        var colorFieldPlugins;
        if (this.colorManager) {
            colorFieldPlugins = [new this.colorManager];
        }

        this.items = [{
            xtype: "fieldset",
            title: this.titleText,
            autoHeight: true,
            checkboxToggle: this.checkboxToggle,
            collapsed: this.checkboxToggle === true &&
                this.symbolizer.stroke === false,
            hideMode: "offsets",
            defaults: {
                width: 100 // TODO: move to css
            },
            items: [{
                xtype: "combo",
                name: "style",
                fieldLabel: this.styleText,
                store: new Ext.data.SimpleStore({
                    data: this.dashStyles,
                    fields: ["value", "display"]
                }),
                displayField: "display",
                valueField: "value",
                value: this.getDashArray(this.symbolizer.strokeDashstyle) || OpenLayers.Renderer.defaultSymbolizer.strokeDashstyle,
                mode: "local",
                allowBlank: true,
                triggerAction: "all",
                editable: false,
                listeners: {
                    select: function(combo, record) {
                        this.symbolizer.strokeDashstyle = record.get("value");
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "gxp_colorfield",
                name: "color",
                fieldLabel: this.colorText,
                emptyText: OpenLayers.Renderer.defaultSymbolizer.strokeColor,
                value: this.symbolizer.strokeColor,
                defaultBackground: this.defaultColor ||
                    OpenLayers.Renderer.defaultSymbolizer.strokeColor,
                plugins: colorFieldPlugins,
                listeners: {
                    valid: function(field) {
                        var newValue = field.getValue();
                        var modified = this.symbolizer.strokeColor != newValue;
                        this.symbolizer.strokeColor = newValue;
                        modified && this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "numberfield",
                name: "width",
                fieldLabel: this.widthText,
                allowNegative: false,
                emptyText: OpenLayers.Renderer.defaultSymbolizer.strokeWidth,
                value: this.symbolizer.strokeWidth,
                listeners: {
                    change: function(field, value) {
                        value = parseFloat(value);
                        if (isNaN(value)) {
                            delete this.symbolizer.strokeWidth;
                        } else {
                            this.symbolizer.strokeWidth = value;
                        }
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "slider",
                name: "opacity",
                fieldLabel: this.opacityText,
                values: [(("strokeOpacity" in this.symbolizer) ? this.symbolizer.strokeOpacity : OpenLayers.Renderer.defaultSymbolizer.strokeOpacity) * 100],
                isFormField: true,
                listeners: {
                    changecomplete: function(slider, value) {
                        this.symbolizer.strokeOpacity = value / 100;
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                },
                plugins: [
                    new GeoExt.SliderTip({
                        getText: function(thumb) {
                            return thumb.value + "%";
                        }
                    })
                ]
            }],
            listeners: {
                "collapse": function() {
                    if (this.symbolizer.stroke !== false) {
                        this.symbolizer.stroke = false;
                        this.fireEvent("change", this.symbolizer);
                    }
                },
                "expand": function() {
                    this.symbolizer.stroke = true;
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            }
        }];

        this.addEvents(
            /**
             * Event: change
             * Fires before any field blurs if the field value has changed.
             *
             * Listener arguments:
             * symbolizer - {Object} A symbolizer with stroke related properties
             *     updated.
             */
            "change"
        ); 
 
        gxp.StrokeSymbolizer.superclass.initComponent.call(this);
        
    },

    getDashArray: function(style) {
        var array;
        if (style) {
            var parts = style.split(/\s+/);
            var ratio = parts[0] / parts[1];
            if (!isNaN(ratio)) {
                array = ratio >= 1 ? "4 4" : "2 4";
            }
        }
        return array;
    }
    
    
    
});

/** api: xtype = gxp_strokesymbolizer */
Ext.reg('gxp_strokesymbolizer', gxp.StrokeSymbolizer); 
