/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include widgets/form/FilterField.js
 */

/** api: (define)
 *  module = gxp
 *  class = FilterBuilder
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: FilterBuilder(config)
 *   
 *      Create a panel for assembling a filter.
 */
gxp.FilterBuilder = Ext.extend(Ext.Container, {

    /** api: config[builderTypeNames]
     *  ``Array``
     *  A list of labels that correspond to builder type constants.
     *  These will be the option names available in the builder type combo.
     *  Default is ``["any", "all", "none", "not all"]``.
     */
    builderTypeNames: ["any", "all", "none", "not all"],
    
    /** api: config[allowedBuilderTypes]
     *  ``Array``
     *  List of builder type constants.  Default is
     *  ``[ANY_OF, ALL_OF, NONE_OF]``.
     */
    allowedBuilderTypes: null,
    
    /** api: config[allowBlank]
     *  ``Boolean`` Do we allow blank FilterFields? It is safe to say true
     *  here, but for compatibility reasons with old applications, the default
     *  is false.
     */
    allowBlank: false,
    
    /** api: config[preComboText]
     *  ``String``
     *  String to display before filter type combo.  Default is ``"Match"``.
     */
    preComboText: "Match",

    /** api: config[postComboText]
     *  ``String``
     *  String to display after filter type combo.  Default is
     *  ``"of the following:"``.
     */
    postComboText: "of the following:",

    /** api: config[cls]
     *  ``String``
     *  The CSS class to be added to this panel's element (defaults to
     *  ``"gxp-filterbuilder"``).
     */
    cls: "gxp-filterbuilder",
    
    /** api: config[filter]
     *  ``OpenLayers.Filter``
     *  Filter to initialize the component with
     */

    /** private: property[builderType]
     */
    builderType: null,

    /** private: property[childFilterContainer]
     */
    childFilterContainer: null,
    
    /** private: property[customizeFilterOnInit]
     */
    customizeFilterOnInit: true,
    
    /** i18n */
    addConditionText: "add condition",
    addGroupText: "add group",
    removeConditionText: "remove condition",

    /** api: config[allowGroups]
     *  ``Boolean``
     *  Allow groups of conditions to be added.  Default is ``true``.
     *  If ``false``, only individual conditions (non-logical filters) can
     *  be added.
     */
    allowGroups: true,

    initComponent: function() {
        var defConfig = {
            defaultBuilderType: gxp.FilterBuilder.ANY_OF
        };
        Ext.applyIf(this, defConfig);
        
        if(this.customizeFilterOnInit) {
            this.filter = this.customizeFilter(this.filter);
        }
        
        this.builderType = this.getBuilderType();
        
        this.items = [{
            xtype: "container",
            layout: "form",
            ref: "form",
            defaults: {anchor: "100%"},
            hideLabels: true,
            items: [{
                xtype: "compositefield",
                style: "padding-left: 2px",
                items: [{
                    xtype: "label",
                    style: "padding-top: 0.3em",
                    text: this.preComboText
                }, this.createBuilderTypeCombo(), {
                    xtype: "label",
                    style: "padding-top: 0.3em",
                    text: this.postComboText
                }]
            }, this.createChildFiltersPanel(), {
                xtype: "toolbar",
                items: this.createToolBar()
            }]
        
        }];
        
        this.addEvents(
            /**
             * Event: change
             * Fires when the filter changes.
             *
             * Listener arguments:
             * builder - {gxp.FilterBuilder} This filter builder.  Call
             *     ``getFilter`` to get the updated filter.
             */
            "change"
        ); 

        gxp.FilterBuilder.superclass.initComponent.call(this);
    },

    /** private: method[createToolBar]
     */
    createToolBar: function() {
        var bar = [{
            text: this.addConditionText,
            iconCls: "add",
            handler: function() {
                this.addCondition();
            },
            scope: this
        }];
        if(this.allowGroups) {
            bar.push({
                text: this.addGroupText,
                iconCls: "add",
                handler: function() {
                    this.addCondition(true);
                },
                scope: this
            });
        }
        return bar;
    },
    
    /** api: method[getFilter]
     *  :return: ``OpenLayers.Filter``
     *  
     *  Returns a filter that fits the model in the Filter Encoding
     *  specification.  Use this method instead of directly accessing
     *  the ``filter`` property.  Return will be ``false`` if any child
     *  filter does not have a type, property, or value.
     */
    getFilter: function() {
        var filter;
        if(this.filter) {
            filter = this.filter.clone();
            if(filter instanceof OpenLayers.Filter.Logical) {
                filter = this.cleanFilter(filter);
            }
        }
        return filter;
    },
    
    /** private: method[cleanFilter]
     *  :arg filter: ``OpenLayers.Filter.Logical``
     *  :return: ``OpenLayers.Filter`` An equivalent filter to the input, where
     *      all binary logical filters have more than one child filter.  Returns
     *      false if a filter doesn't have non-null type, property, or value.
     *  
     *  Ensures that binary logical filters have more than one child.
     */
    cleanFilter: function(filter) {
        if(filter instanceof OpenLayers.Filter.Logical) {
            if(filter.type !== OpenLayers.Filter.Logical.NOT &&
               filter.filters.length === 1) {
                filter = this.cleanFilter(filter.filters[0]);
            } else {
                var child;
                for(var i=0, len=filter.filters.length; i<len; ++i) {
                    child = filter.filters[i];
                    if(child instanceof OpenLayers.Filter.Logical) {
                        child = this.cleanFilter(child);
                        if(child) {
                            filter.filters[i] = child;
                        } else {
                            filter = child;
                            break;
                        }
                    } else if(!child || child.type === null ||
                              child.property === null || child[filter.type === OpenLayers.Filter.Comparison.BETWEEN ? "lowerBoundary" : "value"] === null) {
                        filter = false;
                        break;
                    }
                }
            }
        } else {
            if(!filter || filter.type === null || filter.property === null ||
               filter[filter.type === OpenLayers.Filter.Comparison.BETWEEN ? "lowerBoundary" : "value"] === null) {
                filter = false;
            }
        }
        return filter;
    },
    
    /** private: method[customizeFilter]
     *  :arg filter: ``OpenLayers.Filter``  This filter will not
     *      be modified.  Register for events to receive an updated filter, or
     *      call ``getFilter``.
     *  :return: ``OpenLayers.Filter``  A filter that fits the model used by
     *      this builder.
     *  
     *  Create a filter that fits the model for this filter builder.  This filter
     *  will not necessarily meet the Filter Encoding specification.  In
     *  particular, filters representing binary logical operators may not
     *  have two child filters.  Use the <getFilter> method to return a
     *  filter that meets the encoding spec.
     */
    customizeFilter: function(filter) {
        if(!filter) {
            filter = this.wrapFilter(this.createDefaultFilter());
        } else {
            filter = this.cleanFilter(filter);
            var child, i, len;
            switch(filter.type) {
                case OpenLayers.Filter.Logical.AND:
                case OpenLayers.Filter.Logical.OR:
                    if(!filter.filters || filter.filters.length === 0) {
                        // give the filter children if it has none
                        filter.filters = [this.createDefaultFilter()];
                    } else {
                        for(i=0, len=filter.filters.length; i<len; ++i) {
                            child = filter.filters[i];
                            if(child instanceof OpenLayers.Filter.Logical) {
                                filter.filters[i] = this.customizeFilter(child);
                            }
                        }
                    }
                    // wrap in a logical OR
                    filter = new OpenLayers.Filter.Logical({
                        type: OpenLayers.Filter.Logical.OR,
                        filters: [filter]
                    });
                    break;
                case OpenLayers.Filter.Logical.NOT:
                    if(!filter.filters || filter.filters.length === 0) {
                        filter.filters = [
                            new OpenLayers.Filter.Logical({
                                type: OpenLayers.Filter.Logical.OR,
                                filters: [this.createDefaultFilter()]
                            })
                        ];
                    } else {
                        // NOT filters should have one child only
                        child = filter.filters[0];
                        if(child instanceof OpenLayers.Filter.Logical) {
                            if(child.type !== OpenLayers.Filter.Logical.NOT) {
                                // check children of AND and OR
                                var grandchild;
                                for(i=0, len=child.filters.length; i<len; ++i) {
                                    grandchild = child.filters[i];
                                    if(grandchild instanceof OpenLayers.Filter.Logical) {
                                        child.filters[i] = this.customizeFilter(grandchild);
                                    }
                                }
                            } else {
                                // silly double negative
                                if(child.filters && child.filters.length > 0) {
                                    filter = this.customizeFilter(child.filters[0]);
                                } else {
                                    filter = this.wrapFilter(this.createDefaultFilter());
                                }
                            }
                        } else {
                            // non-logical child of NOT should be wrapped
                            var type;
                            if(this.defaultBuilderType === gxp.FilterBuilder.NOT_ALL_OF) {
                                type = OpenLayers.Filter.Logical.AND;
                            } else {
                                type = OpenLayers.Filter.Logical.OR;
                            }
                            filter.filters = [
                                new OpenLayers.Filter.Logical({
                                    type: type,
                                    filters: [child]
                                })
                            ];
                        }
                    }
                    break;
                default:
                    // non-logical filters get wrapped
                    filter = this.wrapFilter(filter);
                    break;
            }
        }
        return filter;
    },
    
    createDefaultFilter: function() {
        return new OpenLayers.Filter.Comparison();
    },
    
    /** private: method[wrapFilter]
     *  :arg filter: ``OpenLayers.Filter`` A non-logical filter.
     *  :return: ``OpenLayers.Filter`` A wrapped version of the input filter.
     *  
     *  Given a non-logical filter, this creates parent filters depending on
     *  the ``defaultBuilderType``.
     */
    wrapFilter: function(filter) {
        var type;
        if(this.defaultBuilderType === gxp.FilterBuilder.ALL_OF) {
            type = OpenLayers.Filter.Logical.AND;
        } else {
            type = OpenLayers.Filter.Logical.OR;
        }
        return new OpenLayers.Filter.Logical({
            type: OpenLayers.Filter.Logical.OR,
            filters: [
                new OpenLayers.Filter.Logical({
                    type: type, filters: [filter]
                })
            ]
        });
    },
    
    /** private: method[addCondition]
     *  Add a new condition or group of conditions to the builder.  This
     *  modifies the filter and adds a panel representing the new condition
     *  or group of conditions.
     */
    addCondition: function(group) {
        var filter, type;
        if(group) {
            type = "gxp_filterbuilder";
            filter = this.wrapFilter(this.createDefaultFilter());
        } else {
            type = "gxp_filterfield";
            filter = this.createDefaultFilter();
        }
        var newChild = this.newRow({
            xtype: type,
            filter: filter,
            columnWidth: 1,
            attributes: this.attributes,
            allowBlank: group ? undefined : this.allowBlank,
            customizeFilterOnInit: group && false,
            listeners: {
                change: function() {
                    this.fireEvent("change", this);
                },
                scope: this
            }
        });
        this.childFilterContainer.add(newChild);
        this.filter.filters[0].filters.push(filter);
        this.childFilterContainer.doLayout();
    },
    
    /** private: method[removeCondition]
     *  Remove a condition or group of conditions from the builder.  This
     *  modifies the filter and removes the panel representing the condition
     *  or group of conditions.
     */
    removeCondition: function(item, filter) {
        var parent = this.filter.filters[0].filters;
        if(parent.length > 0) {
            parent.remove(filter);
            this.childFilterContainer.remove(item, true);
        }
        if(parent.length === 0) {
            this.addCondition();
        }
        this.fireEvent("change", this);
    },
    
    createBuilderTypeCombo: function() {
        var types = this.allowedBuilderTypes || [
            gxp.FilterBuilder.ANY_OF, gxp.FilterBuilder.ALL_OF,
            gxp.FilterBuilder.NONE_OF
        ];
        var numTypes = types.length;
        var data = new Array(numTypes);
        var type;
        for(var i=0; i<numTypes; ++i) {
            type = types[i];
            data[i] = [type, this.builderTypeNames[type]];
        }
        return {
            xtype: "combo",
            store: new Ext.data.SimpleStore({
                data: data,
                fields: ["value", "name"]
            }),
            value: this.builderType,
            ref: "../../builderTypeCombo",
            displayField: "name",
            valueField: "value",
            triggerAction: "all",
            mode: "local",
            listeners: {
                select: function(combo, record) {
                    this.changeBuilderType(record.get("value"));
                    this.fireEvent("change", this);
                },
                scope: this
            },
            width: 60 // TODO: move to css
        };
    },
    
    /** private: method[changeBuilderType]
     *  :arg type: ``Integer`` One of the filter type constants.
     *  
     *  Alter the filter types when the filter type combo changes.
     */
    changeBuilderType: function(type) {
        if(type !== this.builderType) {
            this.builderType = type;
            var child = this.filter.filters[0];
            switch(type) {
                case gxp.FilterBuilder.ANY_OF:
                    this.filter.type = OpenLayers.Filter.Logical.OR;
                    child.type = OpenLayers.Filter.Logical.OR;
                    break;
                case gxp.FilterBuilder.ALL_OF:
                    this.filter.type = OpenLayers.Filter.Logical.OR;
                    child.type = OpenLayers.Filter.Logical.AND;
                    break;
                case gxp.FilterBuilder.NONE_OF:
                    this.filter.type = OpenLayers.Filter.Logical.NOT;
                    child.type = OpenLayers.Filter.Logical.OR;
                    break;
                case gxp.FilterBuilder.NOT_ALL_OF:
                    this.filter.type = OpenLayers.Filter.Logical.NOT;
                    child.type = OpenLayers.Filter.Logical.AND;
                    break;
            }
        }
    },

    /** private: method[createChildFiltersPanel]
     *  :return: ``Ext.Container``
     *  
     *  Create the panel that holds all conditions and condition groups.  Since
     *  this is called after this filter has been customized, we always
     *  have a logical filter with one child filter - that child is also
     *  a logical filter.
     */
    createChildFiltersPanel: function() {
        this.childFilterContainer = new Ext.Container();
        var grandchildren = this.filter.filters[0].filters;
        var grandchild;
        for(var i=0, len=grandchildren.length; i<len; ++i) {
            grandchild = grandchildren[i];
            var fieldCfg = {
                xtype: "gxp_filterfield",
                allowBlank: this.allowBlank,
                columnWidth: 1,
                filter: grandchild,
                attributes: this.attributes,
                listeners: {
                    change: function() {
                        this.fireEvent("change", this);
                    },
                    scope: this
                }
            };
            var containerCfg = Ext.applyIf(
                grandchild instanceof OpenLayers.Filter.Logical ?
                    {
                        xtype: "gxp_filterbuilder"
                    } : {
                        xtype: "container",
                        layout: "form",
                        hideLabels: true,
                        items: fieldCfg
                    }, fieldCfg);
                
            this.childFilterContainer.add(this.newRow(containerCfg));
        }
        return this.childFilterContainer;
    },

    /** private: method[newRow]
     *  :return: ``Ext.Container`` A container that serves as a row in a child
     *  filters panel.
     *  
     *  Generate a "row" for the child filters panel.  This couples another
     *  filter panel or filter builder with a component that allows for
     *  condition removal.
     */
    newRow: function(filterContainer) {
        var ct = new Ext.Container({
            layout: "column",
            items: [{
                xtype: "container",
                width: 28,
                height: 26,
                style: "padding-left: 2px",
                items: {
                    xtype: "button",
                    tooltip: this.removeConditionText,
                    iconCls: "delete",
                    handler: function(btn){
                        this.removeCondition(ct, filterContainer.filter);
                    },
                    scope: this
                }
            }, filterContainer]
        });
        return ct;
    },

    /** private: method[getBuilderType]
     *
     *  :return: ``Integer``  One of the builder type constants.
     *  Determine the builder type based on this filter.
     */
    getBuilderType: function() {
        var type = this.defaultBuilderType;
        if(this.filter) {
            var child = this.filter.filters[0];
            if(this.filter.type === OpenLayers.Filter.Logical.NOT) {
                switch(child.type) {
                    case OpenLayers.Filter.Logical.OR:
                        type = gxp.FilterBuilder.NONE_OF;
                        break;
                    case OpenLayers.Filter.Logical.AND:
                        type = gxp.FilterBuilder.NOT_ALL_OF;
                        break;
                }
            } else {
                switch(child.type) {
                    case OpenLayers.Filter.Logical.OR:
                        type = gxp.FilterBuilder.ANY_OF;
                        break;
                    case OpenLayers.Filter.Logical.AND:
                        type = gxp.FilterBuilder.ALL_OF;
                        break;
                }
            }
        }
        return type;
    },

    /** api: method[setFilter]
     *
     *  :param filter: ``OpenLayers.Filter``
     *
     *  Change the filter associated with this instance.
     */
    setFilter: function(filter) {
        this.filter = this.customizeFilter(filter);
        this.changeBuilderType(this.getBuilderType());
        this.builderTypeCombo.setValue(this.builderType);
        this.form.remove(this.childFilterContainer);
        this.form.insert(1, this.createChildFiltersPanel());
        this.form.doLayout();
        this.fireEvent("change", this);
    }

});

/**
 * Builder Types
 */
gxp.FilterBuilder.ANY_OF = 0;
gxp.FilterBuilder.ALL_OF = 1;
gxp.FilterBuilder.NONE_OF = 2;
gxp.FilterBuilder.NOT_ALL_OF = 3;

/** api: xtype = gxp_filterbuilder */
Ext.reg('gxp_filterbuilder', gxp.FilterBuilder); 
