/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires util.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = WMSRasterStylesDialog
 */

Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: WMSRasterStyleDialog(config)
 *
 *    This plugins extends the :class:`gxp.WMSStylesDialog` to with basic
 *    raster support, for single-band rasters only.
 *
 *    TODO replace this with true raster support instead of squeezing it into
 *    a VectorLegend as if we were dealing with vector styles.
 */
gxp.plugins.WMSRasterStylesDialog = {

    /** private: property[isRaster]
     *  ``Boolean`` Are we dealing with a raster layer with RasterSymbolizer?
     *  This is needed because we create pseudo rules from a RasterSymbolizer's
     *  ColorMap, and for this we need special treatment in some places.
     */
    isRaster: null,

    init: function(target) {
        Ext.apply(target, gxp.plugins.WMSRasterStylesDialog);
    },

    /** private: method[createRule]
     */
    createRule: function() {
        var symbolizers = [
            new OpenLayers.Symbolizer[this.isRaster ? "Raster" : this.symbolType]
        ];
        return new OpenLayers.Rule({symbolizers: symbolizers});
    },

    /** private: method[addRule]
     */
    addRule: function() {
        var legend = this.rulesFieldSet.items.get(0);
        if (this.isRaster) {
            legend.rules.push(this.createPseudoRule());
            // we need either zero or at least two rules
            legend.rules.length == 1 &&
            legend.rules.push(this.createPseudoRule());
            this.savePseudoRules();
        } else {
            this.selectedStyle.get("userStyle").rules.push(
                this.createRule()
            );
            legend.update();
            // mark the style as modified
            this.selectedStyle.store.afterEdit(this.selectedStyle);
        }
        this.updateRuleRemoveButton();
    },

    /** private: method[removeRule]
     */
    removeRule: function() {
        if (this.isRaster) {
            var legend = this.rulesFieldSet.items.get(0);
            var rule = this.selectedRule;
            legend.unselect();
            legend.rules.remove(rule);
            // we need either zero or at least two rules
            legend.rules.length == 1 && legend.rules.remove(legend.rules[0]);
            this.savePseudoRules();
        } else {
            gxp.WMSStylesDialog.prototype.removeRule.apply(this, arguments);
        }
    },

    /** private: method[duplicateRule]
     */
    duplicateRule: function() {
        var legend = this.rulesFieldSet.items.get(0);
        if (this.isRaster) {
            legend.rules.push(this.createPseudoRule({
                quantity: this.selectedRule.name,
                label: this.selectedRule.title,
                color: this.selectedRule.symbolizers[0].fillColor,
                opacity: this.selectedRule.symbolizers[0].fillOpacity
            }));
            this.savePseudoRules();
        } else {
            var newRule = this.selectedRule.clone();
            newRule.name = gxp.util.uniqueName(
                (newRule.title || newRule.name) + " (copy)");
            delete newRule.title;
            this.selectedStyle.get("userStyle").rules.push(
                newRule
            );
            legend.update();
        }
        this.updateRuleRemoveButton();
    },

    editRule: function() {
        this.isRaster ? this.editPseudoRule() :
            gxp.WMSStylesDialog.prototype.editRule.apply(this, arguments);
    },

    /** private: method[editPseudoRule]
     *  Edit a pseudo rule of a RasterSymbolizer's ColorMap.
     */
    editPseudoRule: function() {
        var me = this;
        var rule = this.selectedRule;

        var pseudoRuleDlg = new Ext.Window({
            title: "Color Map Entry: " + rule.name,
            width: 340,
            autoHeight: true,
            modal: true,
            items: [{
                bodyStyle: "padding-top: 5px",
                border: false,
                defaults: {
                    autoHeight: true,
                    hideMode: "offsets"
                },
                items: [{
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
                            width: 70,
                            items: [{
                                xtype: "numberfield",
                                anchor: "95%",
                                value: rule.name,
                                allowBlank: false,
                                fieldLabel: "Quantity",
                                validator: function(value) {
                                    var rules = me.rulesFieldSet.items.get(0).rules;
                                    for (var i=rules.length-1; i>=0; i--) {
                                        if (rule !== rules[i] && rules[i].name == value) {
                                            return "Quantity " + value + " is already defined";
                                        }
                                    }
                                    return true;
                                },
                                listeners: {
                                    valid: function(cmp) {
                                        this.selectedRule.name = String(cmp.getValue());
                                        this.savePseudoRules();
                                    },
                                    scope: this
                                }
                            }]
                        }, {
                            layout: "form",
                            width: 130,
                            items: [{
                                xtype: "textfield",
                                fieldLabel: "Label",
                                anchor: "95%",
                                value: rule.title,
                                listeners: {
                                    valid: function(cmp) {
                                        this.selectedRule.title = cmp.getValue();
                                        this.savePseudoRules();
                                    },
                                    scope: this
                                }
                            }]
                        }, {
                            layout: "form",
                            width: 70,
                            items: [new GeoExt.FeatureRenderer({
                                symbolType: this.symbolType,
                                symbolizers: [rule.symbolizers[0]],
                                isFormField: true,
                                fieldLabel: "Appearance"
                            })]
                        }]
                    }]
                }, {
                    xtype: "gxp_polygonsymbolizer",
                    symbolizer: rule.symbolizers[0],
                    bodyStyle: {"padding": "10px"},
                    border: false,
                    labelWidth: 70,
                    defaults: {
                        labelWidth: 70
                    },
                    listeners: {
                        change: function(symbolizer) {
                            var symbolizerSwatch = pseudoRuleDlg.findByType(GeoExt.FeatureRenderer)[0];
                            symbolizerSwatch.setSymbolizers(
                                [symbolizer], {draw: symbolizerSwatch.rendered}
                            );
                            this.selectedRule.symbolizers[0] = symbolizer;
                            this.savePseudoRules();
                        },
                        scope: this
                    }
                }]
            }]
        });
        // remove stroke fieldset
        var strokeSymbolizer = pseudoRuleDlg.findByType("gxp_strokesymbolizer")[0];
        strokeSymbolizer.ownerCt.remove(strokeSymbolizer);

        pseudoRuleDlg.show();
    },

    /** private: method[savePseudoRules]
     *  Takes the pseudo rules from the legend and adds them as
     *  RasterSymbolizer ColorMap back to the userStyle.
     */
    savePseudoRules: function() {
        var style = this.selectedStyle;
        var legend = this.rulesFieldSet.items.get(0);
        var userStyle = style.get("userStyle");

        var pseudoRules = legend.rules;
        pseudoRules.sort(function(a,b) {
            var left = parseFloat(a.name);
            var right = parseFloat(b.name);
            return left === right ? 0 : (left < right ? -1 : 1);
        });

        var symbolizer = userStyle.rules[0].symbolizers[0];
        symbolizer.colorMap = pseudoRules.length > 0 ?
            new Array(pseudoRules.length) : undefined;
        var pseudoRule;
        for (var i=0, len=pseudoRules.length; i<len; ++i) {
            pseudoRule = pseudoRules[i];
            symbolizer.colorMap[i] = {
                quantity: parseFloat(pseudoRule.name),
                label: pseudoRule.title || undefined,
                color: pseudoRule.symbolizers[0].fillColor || undefined,
                opacity: pseudoRule.symbolizers[0].fill == false ? 0 :
                    pseudoRule.symbolizers[0].fillOpacity
            };
        }
        this.afterRuleChange(this.selectedRule);
    },

    /** private: method[createLegend]
     *  :arg rules: ``Array``
     *  :arg options:
     */
    createLegend: function(rules, options) {
        var R = OpenLayers.Symbolizer.Raster;
        if (R && rules[0] && rules[0].symbolizers[0] instanceof R) {
            this.getComponent("rulesfieldset").setTitle("Color Map Entries");
            this.isRaster = true;
            this.addRasterLegend(rules, options);
        } else {
            this.isRaster = false;
            this.addVectorLegend(rules);
        }
    },

    /** private: method[addRasterLegend]
     *  :arg rules: ``Array``
     *  :arg options: ``Object`` Additional options for this method.
     *  :returns: ``GeoExt.VectorLegend`` the legend that was created
     *
     *  Creates the vector legend for the pseudo rules that are created from
     *  the RasterSymbolizer of the first rule and adds it to the rules
     *  fieldset.
     *
     *  Supported options:
     *
     *  * selectedRuleIndex: ``Number`` The index of a pseudo rule to select
     *    in the legend.
     */
    addRasterLegend: function(rules, options) {
        options = options || {};
        //TODO raster styling support is currently limited to one rule, and
        // we can only handle a color map. No band selection and other stuff.
        var symbolizer = rules[0].symbolizers[0];
        var colorMap = symbolizer.colorMap || [];
        var pseudoRules = [];
        var colorMapEntry;
        for (var i=0, len=colorMap.length; i<len; i++) {
            pseudoRules.push(this.createPseudoRule(colorMap[i]));
        }
        this.selectedRule = options.selectedRuleIndex != null ?
            pseudoRules[options.selectedRuleIndex] : null;
        return this.addVectorLegend(pseudoRules, {
            symbolType: "Polygon",
            enableDD: false
        });
    },

    /** private: method[createPseudoRule]
     *  :arg colorMapEntry: ``Object``
     *
     *  Creates a pseudo rule from a ColorMapEntry.
     */
    createPseudoRule: function(colorMapEntry) {
        var quantity = -1;
        if (!colorMapEntry) {
            var fieldset = this.rulesFieldSet;
            if (fieldset.items) {
                rules = fieldset.items.get(0).rules;
                for (var i=rules.length-1; i>=0; i--) {
                    quantity = Math.max(quantity, parseFloat(rules[i].name));
                }
            }
        }
        colorMapEntry = Ext.applyIf(colorMapEntry || {}, {
            quantity: ++quantity,
            color: "#000000",
            opacity: 1
        });
        return new OpenLayers.Rule({
            title: colorMapEntry.label,
            name: String(colorMapEntry.quantity),
            symbolizers: [new OpenLayers.Symbolizer.Polygon({
                fillColor: colorMapEntry.color,
                fillOpacity: colorMapEntry.opacity,
                stroke: false,
                fill: colorMapEntry.opacity !== 0
            })]
        });
    },

    /** private: method[updateRuleRemoveButton]
     *  Enable/disable the "Remove" button to make sure that we don't delete
     *  the last rule.
     */
    updateRuleRemoveButton: function() {
        this.rulesToolbar.items.get(1).setDisabled(!this.selectedRule ||
            (this.isRaster === false &&
                this.rulesFieldSet.items.get(0).rules.length <= 1));
    }

};

/** api: ptype = gxp_wmsrasterstylesdialog */
Ext.preg("gxp_wmsrasterstylesdialog", gxp.plugins.WMSRasterStylesDialog);
