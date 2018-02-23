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
 *  class = FillSymbolizer
 *  base_link = `Ext.FormPanel <http://extjs.com/deploy/dev/docs/?class=Ext.FormPanel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: FillSymbolizer(config)
 *   
 *      Form for configuring a symbolizer fill.
 */
gxp.FillSymbolizer = Ext.extend(Ext.FormPanel, {
    
    /** api: config[symbolizer]
     *  ``Object``
     *  A symbolizer object that will be used to fill in form values.
     *  This object will be modified when values change.  Clone first if
     *  you do not want your symbolizer modified.
     */
    symbolizer: null,

    /** api: config[colorProperty]
     *  ``String`` The property that should be set on the symbolizer to
     *  represent the fill color. Defaults to fillColor. But can also be
     *  set to fontColor for labels.
     */
    colorProperty: "fillColor",

    /** api: config[opacityProperty]
     *  ``String`` The property that should be set on the symbolizer to
     *  represent the fill opacity. Defaults to fillOpacity. But can also be
     *  set to fontOpacity for labels.
     */
    opacityProperty: "fillOpacity",
    
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
     *  color will be displayed when no fillColor value for the symbolizer
     *  is available. Defaults to the ``fillColor`` property of
     *  ``OpenLayers.Renderer.defaultSymbolizer``.
     */
    defaultColor: null,

    border: false,
    
    /** i18n */
    fillText: "Fill",
    colorText: "Color",
    opacityText: "Opacity",
    
    initComponent: function() {
        
        if(!this.symbolizer) {
            this.symbolizer = {};
        }
        
        var colorFieldPlugins;
        if (this.colorManager) {
            colorFieldPlugins = [new this.colorManager()];
        }

        var sliderValue = 100;
        if (this.opacityProperty in this.symbolizer) {
            sliderValue = this.symbolizer[this.opacityProperty];
        }
        else if (OpenLayers.Renderer.defaultSymbolizer[this.opacityProperty]) {
            sliderValue = OpenLayers.Renderer.defaultSymbolizer[this.opacityProperty]*100;
        }
        
        this.items = [{
            xtype: "fieldset",
            title: this.fillText,
            autoHeight: true,
            checkboxToggle: this.checkboxToggle,
            collapsed: this.checkboxToggle === true &&
                this.symbolizer.fill === false,
            hideMode: "offsets",
            defaults: {
                width: 100 // TODO: move to css
            },
            items: [{
                xtype: "gxp_colorfield",
                fieldLabel: this.colorText,
                name: "color",
                emptyText: OpenLayers.Renderer.defaultSymbolizer[this.colorProperty],
                value: this.symbolizer[this.colorProperty],
                defaultBackground: this.defaultColor ||
                    OpenLayers.Renderer.defaultSymbolizer[this.colorProperty],
                plugins: colorFieldPlugins,
                listeners: {
                    valid: function(field) {
                        var newValue = field.getValue();
                        var modified = this.symbolizer[this.colorProperty] != newValue; 
                        this.symbolizer[this.colorProperty] = newValue;
                        modified && this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "slider",
                fieldLabel: this.opacityText,
                name: "opacity",
                values: [sliderValue],
                isFormField: true,
                listeners: {
                    changecomplete: function(slider, value) {
                        this.symbolizer[this.opacityProperty] = value / 100;
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
                    if (this.symbolizer.fill !== false) {
                        this.symbolizer.fill = false;
                        this.fireEvent("change", this.symbolizer);
                    }
                },
                "expand": function() {
                    this.symbolizer.fill = true;
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
             * symbolizer - {Object} A symbolizer with fill related properties
             *     updated.
             */
            "change"
        ); 

        gxp.FillSymbolizer.superclass.initComponent.call(this);
        
    }
    
    
});

/** api: xtype = gxp_fillsymbolizer */
Ext.reg('gxp_fillsymbolizer', gxp.FillSymbolizer);
