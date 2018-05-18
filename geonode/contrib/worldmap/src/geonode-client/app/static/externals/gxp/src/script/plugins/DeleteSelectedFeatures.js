/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = DeleteSelectedFeatures
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: DeleteSelectedFeatures(config)
 *
 *    Plugin for deleting selected features
 */
gxp.plugins.DeleteSelectedFeatures = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_deleteselectedfeatures */
    ptype: "gxp_deleteselectedfeatures",
    
    /** api: config[deleteMsgTitle]
     *  ``String``
     *  Text for delete confirmation window title (i18n).
     */
    deleteMsgTitle: "Delete",

    /** api: config[deleteFeaturesMsg]
     *  ``String``
     *  Text for delete confirmation message with multiple features (i18n).
     */
    deleteFeaturesMsg: "Are you sure you want to delete {0} selected features?",
    
    /** api: config[deleteFeatureMsg]
     *  ``String``
     *  Text for delete confirmation message with a single feature (i18n).
     */
    deleteFeatureMsg: "Are you sure you want to delete the selected feature?",

    /** api: config[menuText]
     *  ``String``
     *  Text for zoom menu item (i18n).
     */
    menuText: "Delete selected features",
    
    /** api: config[buttonText]
     *  ``String`` Text for the button label
     */

    /** api: config[tooltip]
     *  ``String``
     *  Text for zoom action tooltip (i18n).
     */
    tooltip: "Delete the currently selected features",
    
    /** api: config[featureManager]
     *  ``String`` id of the :class:`gxp.plugins.FeatureManager` to look for
     *  selected features
     */
    
    /** private: property[iconCls]
     */
    iconCls: "delete",
    
    /** api: method[addActions]
     */
    addActions: function() {
        var actions = gxp.plugins.DeleteSelectedFeatures.superclass.addActions.apply(this, [{
            text: this.buttonText,
            menuText: this.menuText,
            iconCls: this.iconCls,
            tooltip: this.tooltip,
            handler: this.deleteFeatures,
            scope: this
        }]);
        actions[0].disable();

        var layer = this.target.tools[this.featureManager].featureLayer;
        layer.events.on({
            "featureselected": function() {
                actions[0].isDisabled() && actions[0].enable();
            },
            "featureunselected": function() {
                layer.selectedFeatures.length == 0 && actions[0].disable();
            }
        });
        
        return actions;
    },
    
    deleteFeatures: function() {
        var featureManager = this.target.tools[this.featureManager];
        var features = featureManager.featureLayer.selectedFeatures;
        Ext.Msg.show({
            title: this.deleteMsgTitle,
            msg: features.length > 1 ?
                String.format(this.deleteFeaturesMsg, features.length) :
                this.deleteFeatureMsg,
            buttons: Ext.Msg.YESNO,
            fn: function(button) {
                if (button === "yes") {
                    var store = featureManager.featureStore;
                    for (var feature, i=features.length-1; i>=0; --i) {
                        feature = features[i];
                        feature.layer.selectedFeatures.remove(feature);
                        feature.layer.events.triggerEvent("featureunselected", {feature: feature});
                        if (feature.state !== OpenLayers.State.INSERT) { // TODO: remove after http://trac.geoext.org/ticket/141
                            feature.state = OpenLayers.State.DELETE; // TODO: remove after http://trac.geoext.org/ticket/141
                            store._removing = true; // TODO: remove after http://trac.geoext.org/ticket/141
                        } // TODO: remove after http://trac.geoext.org/ticket/141
                        store.remove(store.getRecordFromFeature(feature));
                        delete store._removing; // TODO: remove after http://trac.geoext.org/ticket/141
                    }
                    store.save();
                }
            },
            scope: this,
            icon: Ext.MessageBox.QUESTION
        });
    }
        
});

Ext.preg(gxp.plugins.DeleteSelectedFeatures.prototype.ptype, gxp.plugins.DeleteSelectedFeatures);
