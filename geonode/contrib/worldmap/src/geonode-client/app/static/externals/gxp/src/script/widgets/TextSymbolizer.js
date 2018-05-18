/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include widgets/FillSymbolizer.js
 * @include widgets/PointSymbolizer.js
 * @include widgets/form/FontComboBox.js
 */

/** api: (define)
 *  module = gxp
 *  class = TextSymbolizer
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: TextSymbolizer(config)
 *   
 *      Form for configuring a text symbolizer.
 */
gxp.TextSymbolizer = Ext.extend(Ext.Panel, {
    
    /** api: config[fonts]
     *  ``Array(String)``
     *  List of fonts for the font combo.  If not set, defaults to the list
     *  provided by the :class:`gxp.FontComboBox`.
     */
    fonts: undefined,
    
    /** api: config[symbolizer]
     *  ``Object``
     *  A symbolizer object that will be used to fill in form values.
     *  This object will be modified when values change.  Clone first if
     *  you do not want your symbolizer modified.
     */
    symbolizer: null,
    
    /** api: config[defaultSymbolizer]
     *  ``Object``
     *  Default symbolizer properties to be used where none provided.
     */
    defaultSymbolizer: null,
    
    /** api: config[attributes]
     *  :class:`GeoExt.data.AttributeStore`
     *  A configured attributes store for use in the filter property combo.
     */
    attributes: null,
    
    /** api: config[colorManager]
     *  ``Function``
     *  Optional color manager constructor to be used as a plugin for the color
     *  field.
     */
    colorManager: null,

    /** private: property[haloCache]
     *  ``Object``
     *  Stores halo properties while fieldset is collapsed.
     */
    haloCache: null,
    
    border: false,    
    layout: "form",
    
    /** i18n */
    labelValuesText: "Label values",
    haloText: "Halo",
    sizeText: "Size",
    priorityText: "Priority",
    labelOptionsText: "Label options",
    autoWrapText: "Auto wrap",
    followLineText: "Follow line",
    maxDisplacementText: "Maximum displacement",
    repeatText: "Repeat",
    forceLeftToRightText: "Force left to right",
    graphicResizeText: "Graphic resize",
    graphicMarginText: "Graphic margin",
    graphicTitle: "Graphic",
    fontColorTitle: "Font color and opacity",
    positioningText: "Label positioning",
    anchorPointText: "Anchor point",
    displacementXText: "Displacement (X-direction)",
    displacementYText: "Displacement (Y-direction)",
    perpendicularOffsetText: "Perpendicular offset",
    priorityHelp: "The higher the value of the specified field, the sooner the label will be drawn (which makes it win in the conflict resolution game)",
    autoWrapHelp: "Wrap labels that exceed a certain length in pixels",
    followLineHelp: "Should the label follow the geometry of the line?",
    maxDisplacementHelp: "Maximum displacement in pixels if label position is busy",
    repeatHelp: "Repeat labels after a certain number of pixels",
    forceLeftToRightHelp: "Labels are usually flipped to make them readable. If the character happens to be a directional arrow then this is not desirable",
    graphic_resizeHelp: "Specifies a mode for resizing label graphics (such as highway shields) to fit the text of the label. The default mode, ‘none’, never modifies the label graphic. In stretch mode, GeoServer will resize the graphic to exactly surround the label text, possibly modifying the image’s aspect ratio. In proportional mode, GeoServer will expand the image to be large enough to surround the text while preserving its original aspect ratio.",
    graphic_marginHelp: "Similar to the margin shorthand property in CSS for HTML, its interpretation varies depending on how many margin values are provided: 1 = use that margin length on all sides of the label 2 = use the first for top & bottom margins and the second for left & right margins. 3 = use the first for the top margin, second for left & right margins, third for the bottom margin. 4 = use the first for the top margin, second for the right margin, third for the bottom margin, and fourth for the left margin.",

    initComponent: function() {

        if(!this.symbolizer) {
            this.symbolizer = {};
        }
        Ext.applyIf(this.symbolizer, this.defaultSymbolizer);

        if (!this.symbolizer.vendorOptions) {
            this.symbolizer.vendorOptions = {};
        }

        this.haloCache = {};

        this.attributes.load();

        var defAttributesComboConfig = {
            xtype: "combo",
            fieldLabel: this.labelValuesText,
            store: this.attributes,
            mode: 'local',
            lastQuery: '',
            editable: false,
            triggerAction: "all",
            allowBlank: false,
            displayField: "name",
            valueField: "name",
            value: this.symbolizer.label && this.symbolizer.label.replace(/^\${(.*)}$/, "$1"),
            listeners: {
                select: function(combo, record) {
                    this.symbolizer.label = "${" + record.get("name") + "}";
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            },
            width: 120
        };
        this.attributesComboConfig = this.attributesComboConfig || {};
        Ext.applyIf(this.attributesComboConfig, defAttributesComboConfig);
        
        this.labelWidth = 80;
        
        this.items = [this.attributesComboConfig, {
            cls: "x-html-editor-tb",
            style: "background: transparent; border: none; padding: 0 0em 0.5em;",
            xtype: "toolbar",
            items: [{
                xtype: "gxp_fontcombo",
                fonts: this.fonts || undefined,
                width: 110,
                value: this.symbolizer.fontFamily,
                listeners: {
                    select: function(combo, record) {
                        this.symbolizer.fontFamily = record.get("field1");
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "tbtext",
                text: this.sizeText + ": "
            }, {
                xtype: "numberfield",
                allowNegative: false,
                emptyText: OpenLayers.Renderer.defaultSymbolizer.fontSize,
                value: this.symbolizer.fontSize,
                width: 30,
                listeners: {
                    change: function(field, value) {
                        value = parseFloat(value);
                        if (isNaN(value)) {
                            delete this.symbolizer.fontSize;
                        } else {
                            this.symbolizer.fontSize = value;
                        }
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                enableToggle: true,
                cls: "x-btn-icon",
                iconCls: "x-edit-bold",
                pressed: this.symbolizer.fontWeight === "bold",
                listeners: {
                    toggle: function(button, pressed) {
                        this.symbolizer.fontWeight = pressed ? "bold" : "normal";
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                enableToggle: true,
                cls: "x-btn-icon",
                iconCls: "x-edit-italic",
                pressed: this.symbolizer.fontStyle === "italic",
                listeners: {
                    toggle: function(button, pressed) {
                        this.symbolizer.fontStyle = pressed ? "italic" : "normal";
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }]
        }, {
            xtype: "gxp_fillsymbolizer",
            fillText: this.fontColorTitle,
            symbolizer: this.symbolizer,
            colorProperty: "fontColor",
            opacityProperty: "fontOpacity",
            checkboxToggle: false,
            autoHeight: true,
            width: 213,
            labelWidth: 70,
            plugins: this.colorManager && [new this.colorManager()],
            listeners: {
                change: function(symbolizer) {
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            }
        }, {
            xtype: "fieldset",
            title: this.graphicTitle,
            checkboxToggle: true,
            hideMode: 'offsets',
            collapsed: !(this.symbolizer.fillColor || this.symbolizer.fillOpacity),
            labelWidth: 70,
            items: [{
                xtype: "gxp_pointsymbolizer",
                symbolizer: this.symbolizer,
                border: false,
                labelWidth: 70
            }, this.createVendorSpecificField({
                name: "graphic-resize",
                xtype: "combo",
                store: ["none", "stretch", "proportional"],
                mode: 'local',
                width: 100,
                triggerAction: 'all',
                fieldLabel: this.graphicResizeText
            }), this.createVendorSpecificField({
                name: "graphic-margin",
                width: 100,
                fieldLabel: this.graphicMarginText,
                xtype: "textfield"
            })],
            listeners: {
                collapse: function() {
                    this.graphicCache = {
                        externalGraphic: this.symbolizer.externalGraphic,
                        fillColor: this.symbolizer.fillColor,
                        fillOpacity: this.symbolizer.fillOpacity,
                        graphicName: this.symbolizer.graphicName,
                        pointRadius: this.symbolizer.pointRadius,
                        rotation: this.symbolizer.rotation,
                        strokeColor: this.symbolizer.strokeColor,
                        strokeWidth: this.symbolizer.strokeWidth,
                        strokeDashStyle: this.symbolizer.strokeDashStyle
                    };
                    delete this.symbolizer.externalGraphic;
                    delete this.symbolizer.fillColor;
                    delete this.symbolizer.fillOpacity;
                    delete this.symbolizer.graphicName;
                    delete this.symbolizer.pointRadius;
                    delete this.symbolizer.rotation;
                    delete this.symbolizer.strokeColor;
                    delete this.symbolizer.strokeWidth;
                    delete this.symbolizer.strokeDashStyle;
                    this.fireEvent("change", this.symbolizer)
                },
                expand: function() {
                    Ext.apply(this.symbolizer, this.graphicCache);
                    /**
                     * Start workaround for
                     * http://projects.opengeo.org/suite/ticket/676
                     */
                    this.doLayout();
                    /**
                     * End workaround for
                     * http://projects.opengeo.org/suite/ticket/676
                     */
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            }
        }, {
            xtype: "fieldset",
            title: this.haloText,
            checkboxToggle: true,
            collapsed: !(this.symbolizer.haloRadius || this.symbolizer.haloColor || this.symbolizer.haloOpacity),
            autoHeight: true,
            labelWidth: 50,
            items: [{
                xtype: "numberfield",
                fieldLabel: this.sizeText,
                anchor: "89%",
                allowNegative: false,
                emptyText: OpenLayers.Renderer.defaultSymbolizer.haloRadius,
                value: this.symbolizer.haloRadius,
                listeners: {
                    change: function(field, value) {
                        value = parseFloat(value);
                        if (isNaN(value)) {
                            delete this.symbolizer.haloRadius;
                        } else {
                            this.symbolizer.haloRadius = value;
                        }
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "gxp_fillsymbolizer",
                symbolizer: {
                    fillColor: ("haloColor" in this.symbolizer) ? this.symbolizer.haloColor : OpenLayers.Renderer.defaultSymbolizer.haloColor,
                    fillOpacity: ("haloOpacity" in this.symbolizer) ? this.symbolizer.haloOpacity : OpenLayers.Renderer.defaultSymbolizer.haloOpacity*100
                },
                defaultColor: OpenLayers.Renderer.defaultSymbolizer.haloColor,
                checkboxToggle: false,
                width: 190,
                labelWidth: 60,
                plugins: this.colorManager && [new this.colorManager()],
                listeners: {
                    change: function(symbolizer) {
                        this.symbolizer.haloColor = symbolizer.fillColor;
                        this.symbolizer.haloOpacity = symbolizer.fillOpacity;
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }],
            listeners: {
                collapse: function() {
                    this.haloCache = {
                        haloRadius: this.symbolizer.haloRadius,
                        haloColor: this.symbolizer.haloColor,
                        haloOpacity: this.symbolizer.haloOpacity
                    };
                    delete this.symbolizer.haloRadius;
                    delete this.symbolizer.haloColor;
                    delete this.symbolizer.haloOpacity;
                    this.fireEvent("change", this.symbolizer)
                },
                expand: function() {
                    Ext.apply(this.symbolizer, this.haloCache);
                    /**
                     * Start workaround for
                     * http://projects.opengeo.org/suite/ticket/676
                     */
                    this.doLayout();
                    /**
                     * End workaround for
                     * http://projects.opengeo.org/suite/ticket/676
                     */                    
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            }
        }, {
            xtype: "fieldset",
            title: this.positioningText,
            checkboxToggle: true,
            collapsed: true,
            autoHeight: true,
            labelWidth: 75,
            defaults: {
                width: 100
            },
            items: [Ext.applyIf({
                fieldLabel: this.anchorPointText,
                value: this.symbolizer.labelAlign || "lb",
                store: [
                    ['lt', 'Left-top'], 
                    ['ct', 'Center-top'], 
                    ['rt', 'Right-top'],
                    ['lm', 'Left-center'],
                    ['cm', 'Center'],
                    ['rm', 'Right-center'],
                    ['lb', 'Left-bottom'],
                    ['cb', 'Center-bottom'],
                    ['rb', 'Right-bottom']
                ],
                listeners: {
                    select: function(combo, record) {
                        this.symbolizer.labelAlign = combo.getValue();
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, this.attributesComboConfig), {
                xtype: "numberfield",
                fieldLabel: this.displacementXText,
                value: this.symbolizer.labelXOffset,
                listeners: {
                    change: function(field, value) {
                        this.symbolizer.labelXOffset = value;
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "numberfield",
                fieldLabel: this.displacementYText,
                value: this.symbolizer.labelYOffset,
                listeners: {
                    change: function(field, value) {
                        this.symbolizer.labelYOffset = value;
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "numberfield",
                fieldLabel: this.perpendicularOffsetText,
                value: this.symbolizer.labelPerpendicularOffset,
                listeners: {
                    change: function(field, value) {
                        if (Ext.isEmpty(value)) {
                            delete this.symbolizer.labelPerpendicularOffset;
                        } else {
                            this.symbolizer.labelPerpendicularOffset = value;
                        }
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }]
        }, {
            xtype: "fieldset",
            title: this.priorityText,
            checkboxToggle: true,
            collapsed: true,
            autoHeight: true,
            labelWidth: 50,
            items: [Ext.applyIf({
                fieldLabel: this.priorityText,
                value: this.symbolizer.priority && this.symbolizer.priority.replace(/^\${(.*)}$/, "$1"),
                allowBlank: true,
                name: 'priority',
                listeners: {
                    select: function(combo, record) {
                        this.symbolizer[combo.name] = "${" + record.get("name") + "}";
                        this.fireEvent("change", this.symbolizer);
                    },
                    render: this.attachHelpToField,
                    scope: this
                }
            }, this.attributesComboConfig)]
        }, {
            xtype: "fieldset",
            title: this.labelOptionsText,
            checkboxToggle: true,
            collapsed: true,
            autoHeight: true,
            labelWidth: 80,
            defaults: {
                width: 100
            },
            items: [
                this.createVendorSpecificField({
                    name: 'autoWrap',
                    allowBlank: false,
                    fieldLabel: this.autoWrapText
                }),
                this.createVendorSpecificField({
                    name: 'followLine', 
                    xtype: 'checkbox', 
                    fieldLabel: this.followLineText
                }),
                this.createVendorSpecificField({
                    name: 'maxDisplacement',
                    fieldLabel: this.maxDisplacementText
                }),
                this.createVendorSpecificField({
                    name: 'repeat',
                    fieldLabel: this.repeatText
                }),
                this.createVendorSpecificField({
                    name: 'forceLeftToRight',
                    xtype: "checkbox",
                    fieldLabel: this.forceLeftToRightText
                })
            ]
        }];

        this.addEvents(
            /**
             * Event: change
             * Fires before any field blurs if the field value has changed.
             *
             * Listener arguments:
             * symbolizer - {Object} A symbolizer with text related properties
             *     updated.
             */
            "change"
        ); 
 
        gxp.TextSymbolizer.superclass.initComponent.call(this);
        
    },

    /**
     * private: method[createVendorSpecificField]
     *  :arg config: ``Object`` config object for the field to create
     *
     *  Create a form field that will generate a VendorSpecific tag.
     */
    createVendorSpecificField: function(config) {
        var listener = function(field, value) {
            // empty VendorOption tags can cause null pointer exceptions in GeoServer
            if (Ext.isEmpty(value)) {
                delete this.symbolizer.vendorOptions[config.name];
            } else {
                this.symbolizer.vendorOptions[config.name] = value;
            }
            this.fireEvent("change", this.symbolizer);
        };
        return Ext.applyIf(config, {
            xtype: "numberfield",
            allowNegative: false,
            value: this.symbolizer.vendorOptions[config.name],
            listeners: {
                render: this.attachHelpToField,
                change: listener,
                check: listener,
                scope: this
            }
        });
    },

    /**
     * private: method[attachHelpToField]
     *  :arg c: ``Ext.Component`` 
     *
     *  Attach a tooltip with extra information to the form field.
     */
    attachHelpToField: function(c) {
        var key = c.name.replace(/-/g, '_') + 'Help';
        Ext.QuickTips.register({
            target: c.getEl(),
            dismissDelay: 20000,
            text: this[key]
        });
    }
    
});

/** api: xtype = gxp_textsymbolizer */
Ext.reg('gxp_textsymbolizer', gxp.TextSymbolizer); 
