/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include data/AutoCompleteReader.js
 * @include data/AutoCompleteProxy.js
 */

/** api: (define)
 *  module = gxp.form
 *  class = AutoCompleteComboBox
 *  base_link = `Ext.form.ComboBox <http://extjs.com/deploy/dev/docs/?class=Ext.form.ComboBox>`_
 */
Ext.namespace("gxp.form");

/** api: constructor
 *  .. class:: AutoCompleteComboBox(config)
 *
 *  Creates an autocomplete combo box that issues queries to a WFS typename.
 *
 */
gxp.form.AutoCompleteComboBox = Ext.extend(Ext.form.ComboBox, {

    /** api: xtype = gxp_autocompletecombo */
    xtype: "gxp_autocompletecombo",

    /** api: config[fieldName]
     *  ``String``
     *  The name of the field/attribute to search on. The "name" of this form
     *  field will also default to fieldName if not provided explicitly. 
     */ 
    fieldName: null,

    /**
     * api: config[featureType]
     * ``String``
     * The WFS featureType to search on.
     */
    featureType: null,

    /**
     * api: config[featurePrefix]
     * ``String``
     * The featurePrefix associated with the featureType.
     */
    featurePrefix: null,

    /**
     * api: config[fieldLabel]
     * ``String``
     * The label to associate with this search field.
     */
    fieldLabel: null,

    /**
     * api: config[geometryName]
     * ``String``
     * The name of the geometry field.
     */
    geometryName: null,

    /**
     * api: config[maxFeatures]
     * ``Integer``
     * The maximum number of features to retrieve in one search action. 
     * Defaults to 500.
     */
    maxFeatures: 500,

    /**
     * api: config[url]
     * ``String``
     * The url of the WFS to search on.
     */
    url: null,

    /**
     * api: config[srsName]
     * ``String``
     * The SRS to use in the WFS GetFeature request.
     */ 
    srsName: null,

    autoHeight: true,

    hideTrigger: true,

    /** api: config[customSortInfo]
     *  ``Object``
     *  Providing custom sort info allows sorting of a single field value by
     *  multiple parts within that value.  For example, a value representing
     *  a street address like "1234 Main Street" would make sense to sort first
     *  by "Main Street" (case insensitive) and then by "1234" (as an integer).
     *  The ``customSortInfo`` object must contain ``matcher`` and ``parts``
     *  properties.
     *
     *  The ``matcher`` value will be used to create a regular expression (with 
     *  ``new RegExp(matcher)``).  This regular expression is assumed to have 
     *  grouping parentheses for each part of the value to be compared.
     * 
     *  The ``parts`` value must be an array with the same length as the number
     *  of groups, or parts of the value to be compared.  Each item in the 
     *  ``parts`` array may have an ``order`` property and a ``sortType``
     *  property.  The optional ``order`` value determines precedence for a part
     *  (e.g. part with order 0 will be compared before part with order 1).
     *  The optional ``sortType`` value must be a string matching one of the
     *  ``Ext.data.SortTypes`` methods (e.g. "asFloat").
     *
     *  Example custom sort info to match addresses like "123 Main St" first by
     *  street name and then by number:
     *
     *  .. code-block:: javascript
     *  
     *      customSortInfo: {
     *          matcher: "^(\\d+)\\s(.*)$",
     *          parts: [
     *              {order: 1, sortType: "asInt"},
     *              {order: 0, sortType: "asUCString"}
     *          ]
     *      }
     */
    customSortInfo: null,

    /** private: method[initComponent]
     *  Override
     */
    initComponent: function() {
        var fields = [{name: this.fieldName}];
        var propertyNames = [this.fieldName];
        if (this.geometryName !== null) {
            fields.push({name: this.geometryName});
            propertyNames.push(this.geometryName);
        }
        if (!this.name) {
            this.name = this.fieldName;
        }
        this.valueField = this.displayField = this.fieldName;
        this.tpl = new Ext.XTemplate('<tpl for="."><div class="x-form-field">','{'+this.fieldName+'}','</div></tpl>');
        this.itemSelector = 'div.x-form-field';
        this.store = new Ext.data.Store({
            fields: fields,
            reader: new gxp.data.AutoCompleteReader({uniqueField: this.fieldName}, propertyNames),
            proxy: new gxp.data.AutoCompleteProxy({protocol: new OpenLayers.Protocol.WFS({
                version: "1.1.0",
                url: this.url,
                featureType: this.featureType,
                featurePrefix: this.featurePrefix,
                srsName: this.srsName,
                propertyNames: propertyNames,
                maxFeatures: this.maxFeatures
            }), setParamsAsOptions: true}),
            sortInfo: this.customSortInfo && {
                field: this.fieldName,
                direction: this.customSortInfo.direction
            }
        });
        if (this.customSortInfo) {
            this.store.createSortFunction = this.createCustomSortFunction();
        }
        return gxp.form.AutoCompleteComboBox.superclass.initComponent.apply(this, arguments);
    },
    
    /** private: method[createCustomSortFunction]
     *  If a ``customSortInfo`` property is provided, this method will be called
     *  to replace the store's ``createSortFunction`` method.
     */
    createCustomSortFunction: function() {

        /** Example customSortInfo:
         *
         *  customSortInfo: {
         *      matcher: "^(\\d+)\\s(.*)$",
         *      parts: [
         *          {order: 1, sortType: "asInt"},
         *          {order: 0, sortType: "asUCString"}
         *      ]
         *  };
         */
        
        var matchRE = new RegExp(this.customSortInfo.matcher);
        var num = this.customSortInfo.parts.length;
        var orderLookup = new Array(num);
        var part;
        for (var i=0; i<num; ++i) {
            part = this.customSortInfo.parts[i];
            orderLookup[i] = {
                index: i,
                sortType: Ext.data.SortTypes[part.sortType || "none"],
                order: part.order || 0
            };
        }
        orderLookup.sort(function(a, b) {
            return a.order - b.order;
        });

        // this method is the replacement for store.createSortFunction
        return function(field, direction) {
            direction = direction || "ASC";
            var directionModifier = direction.toUpperCase() == "DESC" ? -1 : 1;
            
            // this is our custom comparison function that uses the given regex
            // to sort by parts of a single field value
            return function(r1, r2) {
                var d1 = r1.data[field];
                var d2 = r2.data[field];
                var matches1 = matchRE.exec(d1) || [];
                var matches2 = matchRE.exec(d2) || [];
                
                // compare matched parts in order - stopping at first unequal match
                var cmp, v1, v2, lookup;
                for (var i=0, ii=orderLookup.length; i<ii; ++i) {
                    lookup = orderLookup[i];
                    v1 = lookup.sortType(matches1[lookup.index + 1] || d1);
                    v2 = lookup.sortType(matches2[lookup.index + 1] || d2);
                    cmp = (v1 > v2 ? 1 : (v1 < v2 ? -1 : 0));
                    if (cmp) {
                        break;
                    }
                }
                // flip the sign if descending
                return directionModifier * cmp;
            };
        };

    }

});

Ext.reg(gxp.form.AutoCompleteComboBox.prototype.xtype, gxp.form.AutoCompleteComboBox);
