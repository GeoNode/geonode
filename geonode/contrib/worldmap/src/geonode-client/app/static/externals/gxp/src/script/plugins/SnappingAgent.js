/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @require OpenLayers/Control/Snapping.js
 * @require OpenLayers/Strategy/BBOX.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = SnappingAgent
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: SnappingAgent(config)
 *
 *    Plugin for managing snapping while editing.
 */   
gxp.plugins.SnappingAgent = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_snappingagent */
    ptype: "gxp_snappingagent",    
    
    /** api: config[controlOptions]
     *  ``Object`` Options for the ``OpenLayers.Control.Snapping`` used with
     *  this tool.
     */
    
    /** api: config[targets]
     *  ``Array`` Shortcut to the targets control option of the
     *  ``OpenLayers.Control.Snapping`` used with this tool.
     */
    
    /** private: property[controls]
     *  ``Object``
     *  Object property names are editor ids and values are snapping controls 
     *  associated with each editor.
     */ 

    /** private: method[init]
     */
    init: function(target) {
        gxp.plugins.SnappingAgent.superclass.init.apply(this, arguments);
        this.snappingTargets = [];
        this.controls = {};
        this.setSnappingTargets(this.targets);
    },
    
    /** private: method[setSnappingTargets]
     *  :arg targets: ``Array`` List of snapping target configurations.
     */
    setSnappingTargets: function(targets) {
        // clear any previous targets
        this.clearSnappingTargets();
        // configure any given targets
        if (targets) {
            for (var i=0, ii=targets.length; i<ii; ++i) {
                this.addSnappingTarget(targets[i]);
            }
        }
    },
    
    /** private: method[clearSnappingTargets]
     *  Removes all existing snapping targets.  Snapping targets have references
     *  to vector layers that are created in :meth:`addSnappingTarget`.  This 
     *  method destroys those layers.
     */
    clearSnappingTargets: function() {
        var target;
        for (var i=0, ii=this.snappingTargets.length; i<ii; ++i) {
            target = this.snappingTargets[i];
            if (target.layer) {
                target.layer.destroy();
            }
        }
        this.snappingTargets.length = 0;
    },
    
    /** private: method[addSnappingTarget]
     *  :arg snapTarget: ``Object`` Snapping target configuration.
     * 
     *  Create vector layers for the given snapping target based on ``source``
     *  and ``name`` properties.  When the schema for the related feature source
     *  is loaded, a vector layer will be created and set on the snapping
     *  target configuration.  After the snapping target is given a layer, it
     *  will be added to the ``snappingTargets`` list.
     */
    addSnappingTarget: function(snapTarget) {
        snapTarget = Ext.apply({}, snapTarget);

        // Generate a layer for the snapTarget. This layer is not given a 
        // protocol until the feature manager below gives it one.
        var map = this.target.mapPanel.map;
        var layer = new OpenLayers.Layer.Vector(snapTarget.name, {
            strategies: [new OpenLayers.Strategy.BBOX({
                ratio: 1.5,
                // we update manually, because usually the layer is
                // invisble and the strategy would not update anyway
                autoActivate: false
            })],
            displayInLayerSwitcher: false,
            visibility: false,
            minResolution: snapTarget.minResolution,
            maxResolution: snapTarget.maxResolution
        });
        snapTarget.layer = layer;
        this.snappingTargets.push(snapTarget);

        // TODO: Discuss simplifying this.  What we want here is a WFS protocol
        // given a WMS layer config.  We're only using the FeatureManager for 
        // generating the protocol options.
        var featureManager = new gxp.plugins.FeatureManager({
            maxFeatures: null,
            paging: false,
            layer: {
                source: snapTarget.source,
                name: snapTarget.name
            },
            listeners: {
                layerchange: function() {
                    // at this point we have a protocol for the layer
                    layer.protocol = featureManager.featureStore.proxy.protocol;
                    map.addLayer(layer);
                    map.events.on({
                        moveend: function() {
                            this.updateSnappingTarget(snapTarget);
                        },
                        scope: this
                    });
                    this.updateSnappingTarget(snapTarget);
                    this.target.on({
                        featureedit: function(featureManager, layerCfg) {
                            if (layerCfg.name == snapTarget.name && layerCfg.source == snapTarget.source) {
                                this.updateSnappingTarget(snapTarget, {force: true});
                            }
                        },
                        scope: this
                    });
                },
                scope: this
            }
        });

        featureManager.init(this.target);
    },
    
    /** private: method[updateSnappingTarget]
     *  :arg snapTarget: ``Object`` The snapTarget to update
     *  :arg options: ``Object`` 1st argument for
     *      OpenLayers.Strategy.BBOX::update
     *
     *  Checks if features need to be loaded for the snapTarget, and loads them
     *  by calling update on the BBOX strategy.
     */
    updateSnappingTarget: function(snapTarget, options) {
        var min = snapTarget.minResolution || Number.NEGATIVE_INFINITY;
        var max = snapTarget.maxResolution || Number.POSITIVE_INFINITY;
        var resolution = this.target.mapPanel.map.getResolution();
        if (min <= resolution && resolution < max) {
            //TODO unhack this - uses a non-API method (update) and sets a
            // read-only property (visibility) to make the non-API method work
            // in this context.
            var visibility = snapTarget.layer.visibility;
            snapTarget.layer.visibility = true;
            snapTarget.layer.strategies[0].update(options);
            snapTarget.layer.visibility = visibility;
        }
    },
    
    /** private: method[createSnappingControl]
     *  :arg layer: ``OpenLayers.Layer.Vector`` An editable vector layer.
     *
     *  Prepares a snapping control for the provided layer.  All target
     *  configuration is derived from the configuration of this snapping agent.
     */
    createSnappingControl: function(layer) {
        var options = this.initialConfig.controlOptions || this.initialConfig.options;
        var control = new OpenLayers.Control.Snapping(
            Ext.applyIf({layer: layer}, options || {})
        );
        return control;
    },
    
    /** api: method[registerEditor]
     *  :arg editor: :class:`gxp.plugins.FeatureEditor`
     *
     *  Register a feature editor with this snapping agent.  This is called by
     *  feature editors that are configured with a snapping agent.
     */
    registerEditor: function(editor) {
        var featureManager = editor.getFeatureManager();
        var control = this.createSnappingControl(featureManager.featureLayer);
        this.controls[editor.id] = control;
        editor.on({
            layereditable: this.onLayerEditable,
            featureeditable: this.onFeatureEditable,
            scope: this
        });
    },
    
    /** private: method[onLayerEditable]
     *  :arg editor: :class:`gxp.plugins.SnappingAgent`
     *  :arg record: ``GeoExt.data.LayerRecord``
     *  :arg editable: ``Boolean``
     *
     *  Called when ``layereditable`` is fired on the one of the registered 
     *  feature editors.  The purpose of this listener is to set snapping 
     *  targets for the snapping control associated with the given editor
     *  while respecting the snapping target ``restrictedLayer``
     *  property.
     */
    onLayerEditable: function(editor, record, editable) {
        // deactivate all controls except for the one associated with the editor
        var control = this.controls[editor.id];
        if (!editable) {
            control.deactivate();
        } else {
            var targets = [];
            var snappingTarget, layerConfig, include;
            var source = record.get("source");
            var name = record.get("name");
            for (var i=0, ii=this.snappingTargets.length; i<ii; ++i) {
                snappingTarget = this.snappingTargets[i];
                if (snappingTarget.restrictedLayers) {
                    include = false;
                    for (var j=0, jj=snappingTarget.restrictedLayers.length; j<jj; ++j) {
                        layerConfig = snappingTarget.restrictedLayers[j];
                        if (layerConfig.source === source && layerConfig.name === name) {
                            include = true;
                            break;
                        }
                    }
                    if (include) {
                        targets.push(snappingTarget);
                    }
                } else {
                    // no restrictedLayers config, all targets apply
                    targets.push(snappingTarget);
                }
            }
            control.setTargets(targets);
            control.activate();
        }
    },

    /** private: method[onFeatureEditable]
     *  :arg editor: :class:`gxp.plugins.SnappingAgent`
     *  :arg record: ``OpenLayers.Feature.Vector``
     *  :arg editable: ``Boolean``
     *
     *  Called when a feature is selected or unselected for editing.  The 
     *  purpose of this listener is to set or unset any filter on snapping 
     *  targets for the snapping control associated with the given editor
     *  so features are not snapped to themselves during editing.
     */
    onFeatureEditable: function(editor, feature, editable) {
        var manager = editor.getFeatureManager();
        var editableLayer = manager.layerRecord;
        var source = editableLayer.get("source");
        var name = editableLayer.get("name");
        var target, originalFilter, filter;
        // check for editable layer in snapping targets
        for (var i=0, ii=this.snappingTargets.length; i<ii; ++i) {
            target = this.snappingTargets[i];
            if (source === target.source && name === target.name) {
                // editable layer is also snapping target
                originalFilter = this.targets[i].filter;
                if (!feature || !feature.fid || !editable) {
                    // restore the original filter
                    target.filter = originalFilter;
                } else {
                    filter = new OpenLayers.Filter.Logical({
                        type: OpenLayers.Filter.Logical.NOT,
                        filters: [
                            new OpenLayers.Filter.FeatureId({fids: [feature.fid]})
                        ]
                    });
                    if (originalFilter) {
                        target.filter = new OpenLayers.Filter.Logical({
                            type: OpenLayers.Filter.Logical.AND,
                            filters: [originalFilter, filter]
                        });
                    } else {
                        target.filter = filter;
                    }
                }
            }
        }
    }


});

Ext.preg(gxp.plugins.SnappingAgent.prototype.ptype, gxp.plugins.SnappingAgent);
