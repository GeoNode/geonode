/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires OpenLayers/Filter/Comparison.js
 */

/** api: (define)
 *  module = gxp.form
 *  class = ComparisonComboBox
 *  base_link = `Ext.form.ComboBox <http://extjs.com/deploy/dev/docs/?class=Ext.form.ComboBox>`_
 */
Ext.namespace("gxp.form");

/** api: constructor
 *  .. class:: ComparisonComboBox(config)
 *   
 *      A combo box for selecting comparison operators available in OGC
 *      filters.
 */
gxp.form.ComparisonComboBox = Ext.extend(Ext.form.ComboBox, {
    
    allowedTypes: [
        [OpenLayers.Filter.Comparison.EQUAL_TO, "="],
        [OpenLayers.Filter.Comparison.NOT_EQUAL_TO, "<>"],
        [OpenLayers.Filter.Comparison.LESS_THAN, "<"],
        [OpenLayers.Filter.Comparison.GREATER_THAN, ">"],
        [OpenLayers.Filter.Comparison.LESS_THAN_OR_EQUAL_TO, "<="],
        [OpenLayers.Filter.Comparison.GREATER_THAN_OR_EQUAL_TO, ">="],
        [OpenLayers.Filter.Comparison.LIKE, "like"],
        [OpenLayers.Filter.Comparison.BETWEEN, "between"]
    ],

    allowBlank: false,

    mode: "local",

    typeAhead: true,

    forceSelection: true,

    triggerAction: "all",

    width: 50,

    editable: true,
  
    initComponent: function() {
        var defConfig = {
            displayField: "name",
            valueField: "value",
            store: new Ext.data.SimpleStore({
                data: this.allowedTypes,
                fields: ["value", "name"]
            }),
            value: (this.value === undefined) ? this.allowedTypes[0][0] : this.value,
            listeners: {
                // workaround for select event not being fired when tab is hit
                // after field was autocompleted with forceSelection
                "blur": function() {
                    var index = this.store.findExact("value", this.getValue());
                    if (index != -1) {
                        this.fireEvent("select", this, this.store.getAt(index));
                    } else if (this.startValue != null) {
                        this.setValue(this.startValue);
                    }
                }
            }
        };
        Ext.applyIf(this, defConfig);
        
        gxp.form.ComparisonComboBox.superclass.initComponent.call(this);
    }
});

Ext.reg("gxp_comparisoncombo", gxp.form.ComparisonComboBox);
