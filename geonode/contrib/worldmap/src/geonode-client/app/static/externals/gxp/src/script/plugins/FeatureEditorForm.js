/**
 * Copyright (c) 2008-2012 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires GeoExt/widgets/form.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = FeatureEditorForm
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.FormPanel>`_
 */

Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: FeatureEditorForm(config)
 *
 *    Plugin for editing feature attributes in a form.
 */
gxp.plugins.FeatureEditorForm = Ext.extend(Ext.FormPanel, {

    /** api: ptype = gxp_editorform */
    ptype: 'gxp_editorform',

    /** api: config[feature]
     *  ``OpenLayers.Feature.Vector`` The feature being edited/displayed.
     */
    feature: null,

    /** api: config[schema]
     *  ``GeoExt.data.AttributeStore`` Optional. If provided, available
     *  feature attributes will be determined from the schema instead of using
     *  the attributes that the feature has currently set.
     */
    schema: null,

    /** api: config[fieldConfig]
     *  ``Object``
     *  An object with as keys the field names, which will provide the ability
     *  to override the xtype that GeoExt.form created by default based on the
     *  schema. When using a combo xtype, comboStoreData can be used to fill up
     *  the store of the combobox. 
     *  Example is : [['value1', 'display1'], ['value2', 'display2']]
     */
    fieldConfig: null,

    /** api: config[fields]
     *  ``Array``
     *  List of field config names corresponding to feature attributes.  If
     *  not provided, fields will be derived from attributes. If provided,
     *  the field order from this list will be used, and fields missing in the
     *  list will be excluded.
     */
    fields: null,

    /** api: config[excludeFields]
     *  ``Array`` Optional list of field names (case sensitive) that are to be
     *  excluded from the editor plugin.
     */
    excludeFields: null,

    /** api: config[propertyNames]
     *  ``Object`` Property name/display name pairs. If specified, the display
     *  name will be shown in the name column instead of the property name.
     */
    propertyNames: null,

    /** api: config[readOnly]
     *  ``Boolean`` Set to true to disable editing. Default is false.
     */
    readOnly: null,

    monitorValid: true,

    /** private: method[initComponent]
     */
    initComponent : function() {
        this.defaults = Ext.apply(this.defaults || {}, {readOnly: true});

        this.listeners = {
            clientvalidation: function(panel, valid) {
                if (valid && this.getForm().isDirty()) {
                    Ext.apply(this.feature.attributes, this.getForm().getFieldValues());
                    this.featureEditor.setFeatureState(this.featureEditor.getDirtyState());
                }
            },
            scope: this
        };

        gxp.plugins.FeatureEditorForm.superclass.initComponent.call(this);

        if (!this.excludeFields) {
            this.excludeFields = [];
        }

        // all remaining fields
        var excludeFields = [], i, ii;
        for (i=0, ii=this.excludeFields.length; i<ii; ++i) {
            excludeFields[i] = this.excludeFields[i].toLowerCase();
        }
        this.excludeFields = excludeFields;

        var ucFields = this.fields ?
            this.fields.join(",").toUpperCase().split(",") : [];

        var fields = {};
        if (this.schema) {
            this.schema.each(function(r) {
                var name = r.get("name");
                var lower = name.toLowerCase();
                if (this.fields) {
                    if (ucFields.indexOf(name.toUpperCase()) == -1) {
                        this.excludeFields.push(lower);
                    }
                }
                if (this.excludeFields.indexOf(lower) != -1) {
                    return;
                }
                var type = r.get("type");
                if (type.match(/^[^:]*:?((Multi)?(Point|Line|Polygon|Curve|Surface|Geometry))/)) {
                    // exclude gml geometries
                    return;
                }
                var fieldCfg = GeoExt.form.recordToField(r);
                fieldCfg.fieldLabel = this.propertyNames ? (this.propertyNames[name] || fieldCfg.fieldLabel) : fieldCfg.fieldLabel;
                if (this.fieldConfig && this.fieldConfig[name]) {
                    Ext.apply(fieldCfg, this.fieldConfig[name]);
                }
                if (this.feature.attributes[name] !== undefined) {
                    fieldCfg.value = this.feature.attributes[name];
                }
                if (fieldCfg.value && fieldCfg.xtype == "checkbox") {
                    fieldCfg.checked = Ext.isBoolean(fieldCfg.value) ? fieldCfg.value : (fieldCfg.value === "true");
                }
                if (fieldCfg.value && fieldCfg.xtype == "gxp_datefield") {
                    fieldCfg.value = new Date(fieldCfg.value*1000);
                }
                if (fieldCfg.value && fieldCfg.xtype == "datefield") {
                    var dateFormat = "Y-m-d";
                    fieldCfg.format = dateFormat;
                    fieldCfg.value = Date.parseDate(fieldCfg.value.replace(/Z$/, ""), dateFormat);
                }
                if (fieldCfg.xtype === "combo") {
                    Ext.applyIf(fieldCfg, {
                        store: new Ext.data.ArrayStore({
                            fields: ['id', 'value'],
                            data: fieldCfg.comboStoreData
                        }),
                        displayField: 'value',
                        valueField: 'id',
                        mode: 'local',
                        triggerAction: 'all'
                    });
                }
                fields[lower] = fieldCfg;
            }, this);
            this.add(this.reorderFields(fields));
        } else {
            fields = {};
            for (var name in this.feature.attributes) {
                var lower = name.toLowerCase();
                if (this.fields) {
                    if (ucFields.indexOf(name.toUpperCase()) == -1) {
                        this.excludeFields.push(lower);
                    }
                }
                if (this.excludeFields.indexOf(lower) === -1) {
                    var fieldCfg = {
                        xtype: "textfield",
                        fieldLabel: this.propertyNames ? (this.propertyNames[name] || name) : name,
                        name: name,
                        value: this.feature.attributes[name]
                    };
                    fields[lower] = fieldCfg;
                }
            }
            this.add(this.reorderFields(fields));
        }
    },

    /** private: method[reorderFields]
     *
     *  :arg fields: ``Object``
     *  Reorder the fields, if this.fields was defined the order needs to be
     *  taken from this.fields.
     */
    reorderFields: function(fields) {
        var orderedFields = [];
        if (this.fields) {
            for (var i=0,ii=this.fields.length; i<ii; ++i) {
                // a field could have been configured that does not exist
                if (fields[this.fields[i].toLowerCase()]) {
                    orderedFields.push(fields[this.fields[i].toLowerCase()]);
                }
            }
        } else {
            for (var key in fields) {
                orderedFields.push(fields[key]);
            }
        }
        return orderedFields;
    },

    /** private: method[init]
     *
     *  :arg target: ``gxp.FeatureEditPopup`` The feature edit popup 
     *  initializing this plugin.
     */
    init: function(target) {
        this.featureEditor = target;
        this.featureEditor.on("startedit", this.onStartEdit, this);
        this.featureEditor.on("stopedit", this.onStopEdit, this);
        this.featureEditor.on("canceledit", this.onCancelEdit, this);
        this.featureEditor.add(this);
        this.featureEditor.doLayout();
    },

    /** private: method[destroy]
     *  Clean up.
     */
    destroy: function() {
        this.featureEditor.un("startedit", this.onStartEdit, this);
        this.featureEditor.un("stopedit", this.onStopEdit, this);
        this.featureEditor.un("canceledit", this.onCancelEdit, this);
        this.featureEditor = null;
        gxp.plugins.FeatureEditorForm.superclass.destroy.call(this);
    },

    /** private: method[onStartEdit]
     *  When editing starts in the feature edit popup, unmark all fields
     *  as readonly provided we are not in readOnly mode.
     */
    onStartEdit: function() {
        this.getForm().items.each(function(field){
             this.readOnly !== true && field.setReadOnly(false);
        }, this);
    },

    /** private: method[onStopEdit]
     *  When editing stops in the feature edit popup, mark all fields as read only.
     */
    onStopEdit: function() {
        this.getForm().items.each(function(field){
             field.setReadOnly(true);
        });
    },

    /** private: method[onCancelEdit]
     *  :arg panel: ``gxp.FeatureEditPopup``
     *  :arg feature: ``OpenLayers.Feature.Vector``
     *
     *  Reset the form when editing is canceled and the event has a feature.
     */
    onCancelEdit: function(panel, feature) {
        if (feature) {
            var form = this.getForm();
            for (var key in feature.attributes) {
                var field = form.findField(key);
                field && field.setValue(feature.attributes[key]);
            }
        }
    }

});

Ext.preg(gxp.plugins.FeatureEditorForm.prototype.ptype, gxp.plugins.FeatureEditorForm);
