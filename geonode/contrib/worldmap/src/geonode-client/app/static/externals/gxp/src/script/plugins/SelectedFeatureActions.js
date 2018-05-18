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
 *  class = SelectedFeatureActions
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: SelectedFeatureActions(config)
 *
 *    Plugin for creating actions that put an iframe with a url generated from
 *    a template with information from feature attributes or the feature id in
 *    the tool's outputTarget.
 */
 /** api: example
  *  Configuration in the  :class:`gxp.Viewer`:
  *
  *  .. code-block:: javascript
  *
  *    tools: [{
  *        ptype: "gxp_selectedfeatureactions",
  *        featureManager: "myfeaturemanager",
  *        actionTarget: "featuregrid.contextMenu",
  *        actions: [{
  *            menuText: "Search for title",
  *            urlTemplate: "http://google.com/search?q={title}",
  *            iconCls: "google-icon"
  *        }]
  *        }
  *        //...
  *    ]
  */
gxp.plugins.SelectedFeatureActions = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_selectedfeatureactions */
    ptype: "gxp_selectedfeatureactions",
    
    /** api: config[featureManager]
     *  :class:`gxp.plugins.FeatureManager` The feature manager to get the
     *  selected feature from.
     */
    
    /** api: config[actions]
     *  ``Object`` Like actions in :class:`gxp.plugins.Tool`, but with two
     *  additional properties:
     *
     *  * urlTemplate - ``String`` template for the link to follow. To
     *    reference attributes of the selected feature, use "{fieldName}"
     *    in the template. In addition to the attributes, "{fid}" is available
     *    for the feature id (typename prefix removed), and "{layer}" for the
     *    name of the underlying WMS layer (usually prefix:name).
     *  * outputConfig - ``Object`` overrides this tool's outputConfig for
     *    output triggered by the respective action. Useful e.g. for creating
     *    windows with different sizes for each action.
     */
     
    addActions: function() {
        var featureManager = this.target.tools[this.featureManager];
        var len = this.actions.length, actions = new Array(len);
        var tool = this;
        for (var i=0; i<len; ++i) {
            actions[i] = Ext.apply({
                iconCls: "process",
                disabled: true,
                handler: function() {
                    var feature = featureManager.featureLayer.selectedFeatures[0];
                    var tpl = new Ext.Template(this.urlTemplate);
                    var outputConfig = Ext.applyIf(this.outputConfig || {},
                        tool.initialConfig.outputConfig);
                    tool.outputConfig = Ext.apply(outputConfig, {
                        title: this.menuText,
                        bodyCfg: {
                            tag: "iframe",
                            src: tpl.apply(Ext.applyIf({
                                fid: feature.fid.split(".").pop(),
                                layer: featureManager.layerRecord.get("name")
                            }, feature.attributes)),
                            style: {border: "0px none"}
                        }
                    });
                    tool.addOutput();
                }
            }, this.actions[i]);
        }
        featureManager.featureLayer.events.on({
            "featureselected": function(evt) {
                var disabled = evt.feature.layer.selectedFeatures.length != 1;
                for (var i=actions.length-1; i>=0; --i) {
                    actions[i].setDisabled(disabled);
                }
            },
            "featureunselected": function(evt) {
                if (evt.feature.layer.selectedFeatures.length == 0) {
                    for (var i=actions.length-1; i>=0; --i) {
                        actions[i].disable();
                    }
                }
            },
            scope: this
        });
        gxp.plugins.SelectedFeatureActions.superclass.addActions.apply(this, [actions]);
    }
    
});

Ext.preg(gxp.plugins.SelectedFeatureActions.prototype.ptype, gxp.plugins.SelectedFeatureActions);
