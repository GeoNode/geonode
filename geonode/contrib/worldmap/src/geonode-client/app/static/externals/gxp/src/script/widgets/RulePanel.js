/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include widgets/ScaleLimitPanel.js
 * @include widgets/TextSymbolizer.js
 * @include widgets/PolygonSymbolizer.js
 * @include widgets/LineSymbolizer.js
 * @include widgets/PointSymbolizer.js
 * @include widgets/FilterBuilder.js
 */

/** api: (define)
 *  module = gxp
 *  class = RulePanel
 *  base_link = `Ext.TabPanel <http://extjs.com/deploy/dev/docs/?class=Ext.TabPanel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: RulePanel(config)
 *
 *      Create a panel for assembling SLD rules.
 */
gxp.RulePanel = Ext.extend(Ext.TabPanel, {

    /** api: property[fonts]
     *  ``Array(String)`` List of fonts for the font combo.  If not set,
     *      defaults  to the list provided by the <Styler.FontComboBox>.
     */
    fonts: undefined,

    /** api: property[symbolType]
     *  ``String`` One of "Point", "Line", or "Polygon".  If no rule is
     *  provided, default is "Point".
     */
    symbolType: "Point",

    /** api: config[rule]
     *  ``OpenLayers.Rule`` Optional rule provided in the initial
     *  configuration.  If a rule is provided and no `symbolType` is provided,
     *  the symbol type will be derived from the first symbolizer found in the
     *  rule.
     */
    rule: null,

    /** private: property[attributes]
     *  ``GeoExt.data.AttributeStore`` A configured attributes store for use
     *  in the filter property combo.
     */
    attributes: null,

    /** private: property[pointGraphics]
     *  ``Array`` A list of objects to be used as the root of the data for a
     *  JsonStore.  These will become records used in the selection of
     *  a point graphic.  If an object in the list has no "value" property,
     *  the user will be presented with an input to provide their own URL
     *  for an external graphic.  By default, names of well-known marks are
     *  provided.  In addition, the default list will produce a record with
     *  display of "external" that create an input for an external graphic
     *  URL.
     *
     *  Fields:
     *
     *  * display - ``String`` The name to be displayed to the user.
     *  * preview - ``String`` URL to a graphic for preview.
     *  * value - ``String`` Value to be sent to the server.
     *  * mark - ``Boolean`` The value is a well-known name for a mark.  If
     *    false, the value will be assumed to be a url for an external graphic.
     */

    /** private: property[nestedFilters]
     *  ``Boolean`` Allow addition of nested logical filters.  This sets the
     *  allowGroups property of the filter builder.  Default is true.
     */
    nestedFilters: true,

    /** private: property[minScaleDenominatorLimit]
     *  ``Number`` Lower limit for scale denominators.  Default is what you get
     *  when  you assume 20 zoom levels starting with the world in Spherical
     *  Mercator on a single 256 x 256 tile at zoom 0 where the zoom factor is
     *  2.
     */
    minScaleDenominatorLimit: Math.pow(0.5, 19) * 40075016.68 * 39.3701 * OpenLayers.DOTS_PER_INCH / 256,

    /** private: property[maxScaleDenominatorLimit]
     *  ``Number`` Upper limit for scale denominators.  Default is what you get
     *  when you project the world in Spherical Mercator onto a single
     *  256 x 256 pixel tile and assume OpenLayers.DOTS_PER_INCH (this
     *  corresponds to zoom level 0 in Google Maps).
     */
    maxScaleDenominatorLimit: 40075016.68 * 39.3701 * OpenLayers.DOTS_PER_INCH / 256,

    /** private: property [scaleLevels]
     *  ``Number`` Number of scale levels to assume.  This is only for scaling
     *  values exponentially along the slider.  Scale values are not
     *  required to one of the discrete levels.  Default is 20.
     */
    scaleLevels: 20,

    /** private: property[scaleSliderTemplate]
     *  ``String`` Template for the tip displayed by the scale threshold slider.
     *
     *  Can be customized using the following keywords in curly braces:
     *
     *  * zoom - the zoom level
     *  * scale - the scale denominator
     *  * type - "Max" or "Min" denominator
     *  * scaleType - "Min" or "Max" scale (sense is opposite of type)
     *
     *  Default is "{scaleType} Scale 1:{scale}".
     */
    scaleSliderTemplate: "{scaleType} Scale 1:{scale}",

    /** private: method[modifyScaleTipContext]
     *  Called from the multi-slider tip's getText function.  The function
     *  will receive two arguments - a reference to the panel and a data
     *  object.  The data object will have scale, zoom, and type properties
     *  already calculated.  Other properties added to the data object
     *  are available to the <scaleSliderTemplate>.
     */
    modifyScaleTipContext: Ext.emptyFn,

    /** i18n */
    labelFeaturesText: "Label Features",
    labelsText: "Labels",
    basicText: "Basic",
    advancedText: "Advanced",
    limitByScaleText: "Limit by scale",
    limitByConditionText: "Limit by condition",
    symbolText: "Symbol",
    nameText: "Name",


    /** private */
    initComponent: function() {

        var defConfig = {
            plain: true,
            border: false
        };
        Ext.applyIf(this, defConfig);

        if(!this.rule) {
            this.rule = new OpenLayers.Rule({
                name: this.uniqueRuleName()
            });
        } else {
            if (!this.initialConfig.symbolType) {
                this.symbolType = this.getSymbolTypeFromRule(this.rule) || this.symbolType;
            }
        }

        this.activeTab = 0;

        this.textSymbolizer = new gxp.TextSymbolizer({
            symbolizer: this.getTextSymbolizer(),
            attributes: this.attributes,
            fonts: this.fonts,
            listeners: {
                change: function(symbolizer) {
                    this.fireEvent("change", this, this.rule);
                },
                scope: this
            }
        });

        /**
         * The interpretation here is that scale values of zero are equivalent to
         * no scale value.  If someone thinks that a scale value of zero should have
         * a different interpretation, this needs to be changed.
         */
        this.scaleLimitPanel = new gxp.ScaleLimitPanel({
            maxScaleDenominator: this.rule.maxScaleDenominator || undefined,
            limitMaxScaleDenominator: !!this.rule.maxScaleDenominator,
            maxScaleDenominatorLimit: this.maxScaleDenominatorLimit,
            minScaleDenominator: this.rule.minScaleDenominator || undefined,
            limitMinScaleDenominator: !!this.rule.minScaleDenominator,
            minScaleDenominatorLimit: this.minScaleDenominatorLimit,
            scaleLevels: this.scaleLevels,
            scaleSliderTemplate: this.scaleSliderTemplate,
            modifyScaleTipContext: this.modifyScaleTipContext,
            listeners: {
                change: function(comp, min, max) {
                    this.rule.minScaleDenominator = min;
                    this.rule.maxScaleDenominator = max;
                    this.fireEvent("change", this, this.rule);
                },
                scope: this
            }
        });

        this.filterBuilder = new gxp.FilterBuilder({
            allowGroups: this.nestedFilters,
            filter: this.rule && this.rule.filter && this.rule.filter.clone(),
            attributes: this.attributes,
            listeners: {
                change: function(builder) {
                    var filter = builder.getFilter();
                    this.rule.filter = filter;
                    this.fireEvent("change", this, this.rule);
                },
                scope: this
            }
        });




        this.items = [{
            title: this.labelsText,
            autoScroll: true,
            bodyStyle: {"padding": "10px"},
            items: [{
                xtype: "fieldset",
                title: this.labelFeaturesText,
                autoHeight: true,
                checkboxToggle: true,
                collapsed: !this.hasTextSymbolizer(),
                items: [
                    this.textSymbolizer
                ],
                listeners: {
                    collapse: function() {
                        OpenLayers.Util.removeItem(this.rule.symbolizers, this.getTextSymbolizer());
                        this.fireEvent("change", this, this.rule);
                    },
                    expand: function() {
                        this.setTextSymbolizer(this.textSymbolizer.symbolizer);
                        this.fireEvent("change", this, this.rule);
                    },
                    scope: this
                }
            }]
        }];



        if (this.getSymbolTypeFromRule(this.rule) || this.symbolType) {
            this.items = [{
                title: this.basicText,
                autoScroll: true,
                items: [this.createHeaderPanel(), this.createSymbolizerPanel(), this.createClassificationPanel()]
            }, this.items[0], {
                title: this.advancedText,
                defaults: {
                    style: {
                        margin: "7px"
                    }
                },
                autoScroll: true,
                items: [{
                    xtype: "fieldset",
                    title: this.limitByScaleText,
                    checkboxToggle: true,
                    collapsed: !(this.rule && (this.rule.minScaleDenominator || this.rule.maxScaleDenominator)),
                    autoHeight: true,
                    items: [this.scaleLimitPanel],
                    listeners: {
                        collapse: function() {
                            delete this.rule.minScaleDenominator;
                            delete this.rule.maxScaleDenominator;
                            this.fireEvent("change", this, this.rule);
                        },
                        expand: function() {
                            /**
                             * Start workaround for
                             * http://projects.opengeo.org/suite/ticket/676
                             */
                            var tab = this.getActiveTab();
                            this.activeTab = null;
                            this.setActiveTab(tab);
                            /**
                             * End workaround for
                             * http://projects.opengeo.org/suite/ticket/676
                             */
                            var changed = false;
                            if (this.scaleLimitPanel.limitMinScaleDenominator) {
                                this.rule.minScaleDenominator = this.scaleLimitPanel.minScaleDenominator;
                                changed = true;
                            }
                            if (this.scaleLimitPanel.limitMaxScaleDenominator) {
                                this.rule.maxScaleDenominator = this.scaleLimitPanel.maxScaleDenominator;
                                changed = true;
                            }
                            if (changed) {
                                this.fireEvent("change", this, this.rule);
                            }
                        },
                        scope: this
                    }
                }, {
                    xtype: "fieldset",
                    title: this.limitByConditionText,
                    checkboxToggle: true,
                    hidden: this.classifyEnabled,
                    collapsed: !(this.rule && this.rule.filter),
                    autoHeight: true,
                    items: [this.filterBuilder],
                    listeners: {
                        collapse: function(){
                            delete this.rule.filter;
                            this.fireEvent("change", this, this.rule);
                        },
                        expand: function(){
                            var changed = false;
                            this.rule.filter = this.filterBuilder.getFilter();
                            this.fireEvent("change", this, this.rule);
                        },
                        scope: this
                    }
                }
                ]
            }];
        }
        this.items[0].autoHeight = true;




        this.addEvents(
            /** api: events[change]
             *  Fires when any rule property changes.
             *
             *  Listener arguments:
             *  * panel - :class:`gxp.RulePanel` This panel.
             *  * rule - ``OpenLayers.Rule`` The updated rule.
             */
            "change"
        );

        this.on({
            tabchange: function(panel, tab) {
                tab.doLayout();

            },
            afterRender: function() {
                if (this.classifyEnabled) {


                    var symbolizer = this.items.items[0].items.items[1];

                    //Hide fill color
                    var element = Ext.getCmp(Ext.get(symbolizer.id).child('[name=color]').id);
                    element.setVisible(false);

                }
            },
            scope: this
        });

        gxp.RulePanel.superclass.initComponent.call(this);



    },

    /** private: method[hasTextSymbolizer]
     */
    hasTextSymbolizer: function() {
        var candidate, symbolizer;
        for (var i=0, ii=this.rule.symbolizers.length; i<ii; ++i) {
            candidate = this.rule.symbolizers[i];
            if (candidate instanceof OpenLayers.Symbolizer.Text) {
                symbolizer = candidate;
                break;
            }
        }
        return symbolizer;
    },

    /** private: method[getTextSymbolizer]
     *  Get the first text symbolizer in the rule.  If one does not exist,
     *  create one.  If fonts property is defined, used first font as default.
     */
    getTextSymbolizer: function() {
        var symbolizer = this.hasTextSymbolizer();
        if (!symbolizer) {
            symbolizer = new OpenLayers.Symbolizer.Text({graphic: false});
            if (this.fonts) {
                symbolizer.fontFamily = this.fonts[0];
            }
        }
        return symbolizer;
    },

    /** private: method[setTextSymbolizer]
     *  Update the first text symbolizer in the rule.  If one does not exist,
     *  add it.
     */
    setTextSymbolizer: function(symbolizer) {
        var found;
        for (var i=0, ii=this.rule.symbolizers.length; i<ii; ++i) {
            candidate = this.rule.symbolizers[i];
            if (this.rule.symbolizers[i] instanceof OpenLayers.Symbolizer.Text) {
                this.rule.symbolizers[i] = symbolizer;
                found = true;
                break;
            }
        }
        if (!found) {
            this.rule.symbolizers.push(symbolizer);
        }
    },

    /** private: method[uniqueRuleName]
     *  Generate a unique rule name.  This name will only be unique for this
     *  session assuming other names are created by the same method.  If
     *  name needs to be unique given some other context, override it.
     */
    uniqueRuleName: function() {
        return OpenLayers.Util.createUniqueID("rule_");
    },

    /** private: method[createHeaderPanel]
     *  Creates a panel config containing rule name, symbolizer, and scale
     *  constraints.
     */
    createHeaderPanel: function() {
        this.symbolizerSwatch = new GeoExt.FeatureRenderer({
            symbolType: this.symbolType,
            isFormField: true,
            fieldLabel: this.symbolText
        });
        return {
            xtype: "form",
            border: false,
            labelAlign: "top",
            defaults: {border: false},
            style: {"padding": "0.3em 0 0 1em"},
            items: [{
                layout: "column",
                defaults: {
                    border: false,
                    style: {"padding-right": "1em"}
                },
                items: [{
                    layout: "form",
                    width: 150,
                    items: [{
                        xtype: "textfield",
                        hidden: this.classifyEnabled,
                        fieldLabel: this.nameText,
                        anchor: "95%",
                        value: this.rule && (this.rule.title || this.rule.name || ""),
                        listeners: {
                            change: function(el, value) {
                                this.rule.title = value;
                                this.fireEvent("change", this, this.rule);
                            },
                            scope: this
                        }
                    }]
                }, {
                    layout: "form",
                    width: 70,
                    items: [this.symbolizerSwatch]
                }]
            }]
        };
    },

    /** private: method[createSymbolizerPanel]
     */
    createSymbolizerPanel: function() {
        // use first symbolizer that matches symbolType
        var candidate, symbolizer;
        var Type = OpenLayers.Symbolizer[this.symbolType];
        var existing = false;
        if (Type) {
            for (var i=0, ii=this.rule.symbolizers.length; i<ii; ++i) {
                candidate = this.rule.symbolizers[i];
                if (candidate instanceof Type) {
                    existing = true;
                    symbolizer = candidate;
                    break;
                }
            }
            if (!symbolizer) {
                // allow addition of new symbolizer
                symbolizer = new Type({fill: false, stroke: false});
            }
        } else {
            throw new Error("Appropriate symbolizer type not included in build: " + this.symbolType);
        }
        this.symbolizerSwatch.setSymbolizers([symbolizer],
            {draw: this.symbolizerSwatch.rendered}
        );
        var cfg = {
            xtype: "gxp_" + this.symbolType.toLowerCase() + "symbolizer",
            symbolizer: symbolizer,
            bodyStyle: {padding: "10px"},
            border: false,
            labelWidth: 70,
            defaults: {
                labelWidth: 70
            },
            listeners: {
                change: function(symbolizer) {
                    this.symbolizerSwatch.setSymbolizers(
                        [symbolizer], {draw: this.symbolizerSwatch.rendered}
                    );
                    if (!existing) {
                        this.rule.symbolizers.push(symbolizer);
                        existing = true;
                    }
                    this.fireEvent("change", this, this.rule);
                },
                scope: this
            }
        };
        if (this.symbolType === "Point" && this.pointGraphics) {
            cfg.pointGraphics = this.pointGraphics;
        }
        return cfg;

    },

    /** private: method[createClassificationPanel]
     * Interface for specifying classification criteria,
     * Only displays if GeoServer sldService community module
     * is installed.
     */
    createClassificationPanel: function() {

        if (this.classifyEnabled)  {
            this.rule["classify"] = true;
        }

        return new gxp.ClassificationPanel({
            bodyStyle: {padding: "10px"},
            border: false,
            labelWidth: 70,
            defaults: {
                labelWidth: 70
            },
            hidden: !this.classifyEnabled,
            rulePanel: this
        });
    },

    /** private: method[getSymbolTypeFromRule]
     *  :arg rule: `OpenLayers.Rule`
     *  :return: `String` "Point", "Line" or "Polygon" (or undefined if none
     *      of the three.
     *
     *  Determines the symbol type of the first symbolizer of a rule that is
     *  not a text symbolizer
     */
    getSymbolTypeFromRule: function(rule) {
        var candidate, type;
        for (var i=0, ii=rule.symbolizers.length; i<ii; ++i) {
            candidate = rule.symbolizers[i];
            if (!(candidate instanceof OpenLayers.Symbolizer.Text)) {
                type = candidate.CLASS_NAME.split(".").pop();
                break;
            }
        }
        return type;
    }

});

/** api: xtype = gxp_rulepanel */
Ext.reg('gxp_rulepanel', gxp.RulePanel);
