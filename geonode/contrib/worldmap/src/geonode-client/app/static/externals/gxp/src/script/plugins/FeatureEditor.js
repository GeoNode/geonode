/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/ClickableFeatures.js
 * @requires widgets/FeatureEditPopup.js
 * @requires util.js
 * @requires OpenLayers/Control/DrawFeature.js
 * @requires OpenLayers/Handler/Point.js
 * @requires OpenLayers/Handler/Path.js
 * @requires OpenLayers/Handler/Polygon.js
 * @requires OpenLayers/Control/SelectFeature.js
 * @requires GeoExt/widgets/form.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = FeatureEditor
 */

/** api: (extends)
 *  plugins/ClickableFeatures.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: FeatureEditor(config)
 *
 *    Plugin for feature editing. Requires a
 *    :class:`gxp.plugins.FeatureManager`.
 */   
gxp.plugins.FeatureEditor = Ext.extend(gxp.plugins.ClickableFeatures, {
    
    /** api: ptype = gxp_featureeditor */
    ptype: "gxp_featureeditor",
    
    /** api: config[splitButton]
     *  ``Boolean`` If set to true, the actions will be rendered as a single
     *  ``Ext.SplitButton`` instead of two separate ``Ext.Button`` instances,
     *  one for creating new features and one for editing existing features.
     *  Default is false.
     */

    /** private: property[splitButton]
     *  ``Ext.SplitButton`` If :obj:`splitButton` is configured, this will be
     *  the reference to the SplitButton once it was created.
     */
    splitButton: null,

    /** api: config[iconClsAdd]
     *  ``String``
     *  iconCls to use for the add button.
     */
    iconClsAdd: "gxp-icon-addfeature",

    /** api: config[closeOnSave]
     * ``Boolean``
     * If true, close the popup after saving. Defaults to false.
     */
    closeOnSave: false,

    /** api: config[supportAbstractGeometry]
     *  Should we support layers that advertize an abstract geometry type?
     *  In this case, we will provide menu options for digitizing point, line
     *  or polygon features. Default is false.
     */
    supportAbstractGeometry: false,

    /** api: config[supportNoGeometry]
     *  Should we support the ability to create features with no geometry?
     *  This only works when combined with supportAbstractGeometry: true.
     *  Default is false.
     */
    supportNoGeometry: false,

    /** api: config[iconClsEdit]
     *  ``String``
     *  iconCls to use for the edit button.
     */
    iconClsEdit: "gxp-icon-editfeature",

    /** i18n **/
    exceptionTitle: "Save Failed",
    exceptionText: "Trouble saving features",
    pointText: "Point",
    lineText: "Line",
    polygonText: "Polygon",
    noGeometryText: "Event",

    /** api: config[createFeatureActionTip]
     *  ``String``
     *  Tooltip string for create new feature action (i18n).
     */
    createFeatureActionTip: "Create a new feature",

    /** api: config[createFeatureActionText]
     *  ``String``
     *  Create new feature text (i18n).
     */
    createFeatureActionText: "Create",
    
    /** api: config[editFeatureActionTip]
     *  ``String``
     *  Tooltip string for edit existing feature action (i18n).
     */
    editFeatureActionTip: "Edit existing feature",

    /** api: config[editFeatureActionText]
     *  ``String``
     *  Modify feature text (i18n).
     */
    editFeatureActionText: "Modify",
    
    /** api: config[splitButtonText]
     * ``String`` Text for the optional Edit SplitButton (i18n)
     */
    splitButtonText: "Edit",
    
    /** api: config[splitButtonTooltip]
     * ``String`` Tooltip for the optional Edit SplitButton (i18n)
     */
    splitButtonTooltip: "Edit features on selected WMS layer",

    /** api: config[outputTarget]
     *  ``String`` By default, the FeatureEditPopup will be added to the map.
     */
    outputTarget: "map",
    
    /** api: config[snappingAgent]
     *  ``String`` Optional id of the :class:`gxp.plugins.SnappingAgent` to use
     *  with this tool.
     */
    snappingAgent: null,
    
    /** api: config[readOnly]
     *  ``Boolean`` Set to true to use the FeatureEditor merely as a feature
     *  info tool, without editing capabilities. Default is false.
     */
    readOnly: false,

    /** api: config[modifyOnly]
     *  ``Boolean`` Set to true to use the FeatureEditor merely as a feature
     *  modify tool, i.e. there is no option to add new features.
     */
    modifyOnly: false,
    
    /** api: config[showSelectedOnly]
     *  ``Boolean`` If set to true, only selected features will be displayed
     *  on the layer. If set to false, all features (on the current page) will
     *  be. Default is true.
     */
    showSelectedOnly: true,
    
    /** api: config[fields]
     *  ``Array``
     *  List of field config names corresponding to feature attributes.  If
     *  not provided, fields will be derived from attributes. If provided,
     *  the field order from this list will be used, and fields missing in the
     *  list will be excluded.
     */

    /** api: config[excludeFields]
     *  ``Array`` Optional list of field names (case sensitive) that are to be
     *  excluded from the property grid of the FeatureEditPopup.
     */

    /** api: config[roles]
     *  ``Array`` Roles authorized to edit layers. Default is
     *  ["ROLE_ADMINISTRATOR"]
     */
    roles: ["ROLE_ADMINISTRATOR"],
    
    /** private: property[createAction]
     *  ``Ext.Action`` Action for creating new features
     */
    createAction: null,

    /** private: property[editAction]
     *  ``Ext.Action`` Action for editing existing features
     */
    editAction: null,
    
    /** private: property[activeIndex]
     *  ``Integer`` If configured with ``splitButton: true``, this will be the
     *  index of the currently active SplitButton.
     */
    activeIndex: 0,

    /** private: property[drawControl]
     *  ``OpenLayers.Control.DrawFeature``
     */
    drawControl: null,
    
    /** private: property[popup]
     *  :class:`gxp.FeatureEditPopup` FeatureEditPopup for this tool
     */
    popup: null,
    
    /** private: property[schema]
     *  ``GeoExt.data.AttributeStore``
     */
    schema: null,
    

    /** private: method[constructor]
     */
    constructor: function(config) {
        this.addEvents(
            /** api: event[layereditable]
             *  Fired when a layer is selected or unselected in the target 
             *  viewer.  Listeners can use this method to determine when a 
             *  layer is ready for editing.
             *
             *  Listener arguments:
             *
             *  * tool   - :class:`gxp.plugins.FeatureManager` This tool
             *  * record - ``GeoExt.data.LayerRecord`` The selected layer record.
             *    Will be ``null`` if no layer record is selected.
             *  * editable - ``Boolean`` The layer is ready to be edited.
             */
            "layereditable",

            /** api: event[featureeditable]
             *  Fired when a feature is selected or unselected for editing.  
             *  Listeners can use this method to determine when a feature is 
             *  ready for editing.  Beware that this event is fired multiple 
             *  times when a feature is unselected.
             *
             *  Listener arguments:
             *
             *  * tool   - :class:`gxp.plugins.FeatureManager` This tool
             *  * feature - ``OpenLayers.Feature.Vector`` The feature.
             *  * editable - ``Boolean`` The feature is ready to be edited.
             */
            "featureeditable"

        );
        gxp.plugins.FeatureEditor.superclass.constructor.apply(this, arguments);        
    },

    /** private: method[init]
     *  :arg target: ``Object`` The object initializing this plugin.
     */
    init: function(target) {
        gxp.plugins.FeatureEditor.superclass.init.apply(this, arguments);
        this.target.on("authorizationchange", this.onAuthorizationChange, this);
    },

    /** private: method[destroy]
     */
    destroy: function() {
        this.target.un("authorizationchange", this.onAuthorizationChange, this);
        gxp.plugins.FeatureEditor.superclass.destroy.apply(this, arguments);
    },
    
    /** private: method[onAuthorizationChange]
     */
    onAuthorizationChange: function() {
        if (!this.target.isAuthorized(this.roles)) {
            //TODO if a popup is open, this won't take care of closing it when
            // a user logs out.
            this.selectControl.deactivate();
            this.drawControl.deactivate();
        }
        // we don't want to return false here, otherwise we would abort the
        // event chain.
        this.enableOrDisable();
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var popup;
        var featureManager = this.getFeatureManager();
        var featureLayer = featureManager.featureLayer;
        
        var intercepting = false;
        // intercept calls to methods that change the feature store - allows us
        // to persist unsaved changes before calling the original function
        function intercept(mgr, fn) {
            var fnArgs = Array.prototype.slice.call(arguments);
            // remove mgr and fn, which will leave us with the original
            // arguments of the intercepted loadFeatures or setLayer function
            fnArgs.splice(0, 2);
            if (!intercepting && popup && !popup.isDestroyed) {
                if (popup.editing) {
                    function doIt() {
                        intercepting = true;
                        unregisterDoIt.call(this);
                        if (fn === "setLayer") {
                            this.target.selectLayer(fnArgs[0]);
                        } else if (fn === "clearFeatures") {
                            // nothing asynchronous involved here, so let's
                            // finish the caller first before we do anything.
                            window.setTimeout(function() {mgr[fn].call(mgr);});
                        } else {
                            mgr[fn].apply(mgr, fnArgs);
                        }
                    }
                    function unregisterDoIt() {
                        featureManager.featureStore.un("write", doIt, this);
                        popup.un("canceledit", doIt, this);
                        popup.un("cancelclose", unregisterDoIt, this);
                    }
                    featureManager.featureStore.on("write", doIt, this);
                    popup.on({
                        canceledit: doIt,
                        cancelclose: unregisterDoIt,
                        scope: this
                    });
                    popup.close();
                }
                return !popup.editing;
            }
            intercepting = false;
        }
        featureManager.on({
            // TODO: determine where these events should be unregistered
            "beforequery": intercept.createDelegate(this, "loadFeatures", 1),
            "beforelayerchange": intercept.createDelegate(this, "setLayer", 1),
            "beforesetpage": intercept.createDelegate(this, "setPage", 1),
            "beforeclearfeatures": intercept.createDelegate(this, "clearFeatures", 1),
            scope: this
        });
        
        this.drawControl = new OpenLayers.Control.DrawFeature(
            featureLayer,
            OpenLayers.Handler.Point, 
            {
                eventListeners: {
                    featureadded: function(evt) {
                        if (this.autoLoadFeature === true) {
                            this.autoLoadedFeature = evt.feature;
                        }
                    },
                    activate: function() {
                        this.target.doAuthorized(this.roles, function() {
                            featureManager.showLayer(
                                this.id, this.showSelectedOnly && "selected"
                            );
                        }, this);
                    },
                    deactivate: function() {
                        featureManager.hideLayer(this.id);
                    },
                    scope: this
                }
            }
        );
        
        // create a SelectFeature control
        // "fakeKey" will be ignord by the SelectFeature control, so only one
        // feature can be selected by clicking on the map, but allow for
        // multiple selection in the featureGrid
        this.selectControl = new OpenLayers.Control.SelectFeature(featureLayer, {
            clickout: false,
            multipleKey: "fakeKey",
            unselect: function() {
                // TODO consider a beforefeatureunselected event for
                // OpenLayers.Layer.Vector
                if (!featureManager.featureStore.getModifiedRecords().length) {
                    OpenLayers.Control.SelectFeature.prototype.unselect.apply(this, arguments);
                }
            },
            eventListeners: {
                "activate": function() {
                    this.target.doAuthorized(this.roles, function() {
                        if (this.autoLoadFeature === true || featureManager.paging) {
                            this.target.mapPanel.map.events.register(
                                "click", this, this.noFeatureClick
                            );
                        }
                        featureManager.showLayer(
                            this.id, this.showSelectedOnly && "selected"
                        );
                        this.selectControl.unselectAll(
                            popup && popup.editing && {except: popup.feature}
                        );
                    }, this);
                },
                "deactivate": function() {
                    if (this.autoLoadFeature === true || featureManager.paging) {
                        this.target.mapPanel.map.events.unregister(
                            "click", this, this.noFeatureClick
                        );
                    }
                    if (popup) {
                        if (popup.editing) {
                            popup.on("cancelclose", function() {
                                this.selectControl.activate();
                            }, this, {single: true});
                        }
                        popup.on("close", function() {
                            featureManager.hideLayer(this.id);
                        }, this, {single: true});
                        popup.close();
                    } else {
                        featureManager.hideLayer(this.id);
                    }
                },
                scope: this
            }
        });
        
        featureLayer.events.on({
            "beforefeatureremoved": function(evt) {
                if (this.popup && evt.feature === this.popup.feature) {
                    this.selectControl.unselect(evt.feature);
                }
            },
            "featureunselected": function(evt) {
                var feature = evt.feature;
                if (feature) {
                    this.fireEvent("featureeditable", this, feature, false);
                }
                if (feature && feature.geometry && popup && !popup.hidden) {
                    popup.close();
                }
            },
            "beforefeatureselected": function(evt) {
                //TODO decide if we want to allow feature selection while a
                // feature is being edited. If so, we have to revisit the
                // SelectFeature/ModifyFeature setup, because that would
                // require to have the SelectFeature control *always*
                // activated *after* the ModifyFeature control. Otherwise. we
                // must not configure the ModifyFeature control in standalone
                // mode, and use the SelectFeature control that comes with the
                // ModifyFeature control instead.
                if(popup) {
                    return !popup.editing;
                }
            },
            "featureselected": function(evt) {
                var feature = evt.feature;
                if (feature) {
                    this.fireEvent("featureeditable", this, feature, true);
                }
                var featureStore = featureManager.featureStore;
                if(this._forcePopupForNoGeometry === true || (this.selectControl.active && feature.geometry !== null)) {
                    // deactivate select control so no other features can be
                    // selected until the popup is closed
                    if (this.readOnly === false) {
                        this.selectControl.deactivate();
                        // deactivate will hide the layer, so show it again
                        featureManager.showLayer(this.id, this.showSelectedOnly && "selected");
                    }
                    popup = this.addOutput({
                        xtype: "gxp_featureeditpopup",
                        collapsible: true,
                        feature: featureStore.getByFeature(feature),
                        vertexRenderIntent: "vertex",
                        readOnly: this.readOnly,
                        fields: this.fields,
                        excludeFields: this.excludeFields,
                        editing: feature.state === OpenLayers.State.INSERT,
                        schema: this.schema,
                        allowDelete: true,
                        width: 200,
                        height: 250,
                        listeners: {
                            "close": function() {
                                if (this.readOnly === false) {
                                    this.selectControl.activate();
                                }
                                if(feature.layer && feature.layer.selectedFeatures.indexOf(feature) !== -1) {
                                    this.selectControl.unselect(feature);
                                }
                                if (feature === this.autoLoadedFeature) {
                                    if (feature.layer) {
                                        feature.layer.removeFeatures([evt.feature]);
                                    }
                                    this.autoLoadedFeature = null;
                                }
                            },
                            "featuremodified": function(popup, feature) {
                                popup.disable();
                                featureStore.on({
                                    write: {
                                        fn: function() {
                                            if (popup) {
                                                if (popup.isVisible()) {
                                                    popup.enable();
                                                }
                                                if (this.closeOnSave) {
                                                    popup.close();
                                                }
                                            }
                                            var layer = featureManager.layerRecord;
                                            this.target.fireEvent("featureedit", featureManager, {
                                                name: layer.get("name"),
                                                source: layer.get("source")
                                            });
                                        },
                                        single: true
                                    },
                                    exception: {
                                        fn: function(proxy, type, action, options, response, records) {
                                            var msg = this.exceptionText;
                                            if (type === "remote") {
                                                // response is service exception
                                                if (response.exceptionReport) {
                                                    msg = gxp.util.getOGCExceptionText(response.exceptionReport);
                                                }
                                            } else {
                                                // non-200 response from server
                                                msg = "Status: " + response.status;
                                            }
                                            // fire an event on the feature manager
                                            featureManager.fireEvent("exception", featureManager, 
                                                response.exceptionReport || {}, msg, records);
                                            // only show dialog if there is no listener registered
                                            if (featureManager.hasListener("exception") === false && 
                                                featureStore.hasListener("exception") === false) {
                                                    Ext.Msg.show({
                                                        title: this.exceptionTitle,
                                                        msg: msg,
                                                        icon: Ext.MessageBox.ERROR,
                                                        buttons: {ok: true}
                                                    });
                                            }
                                            if (popup && popup.isVisible()) {
                                                popup.enable();
                                                popup.startEditing();
                                            }
                                        },
                                        single: true
                                    },
                                    scope: this
                                });                                
                                if(feature.state === OpenLayers.State.DELETE) {                                    
                                    /**
                                     * If the feature state is delete, we need to
                                     * remove it from the store (so it is collected
                                     * in the store.removed list.  However, it should
                                     * not be removed from the layer.  Until
                                     * http://trac.geoext.org/ticket/141 is addressed
                                     * we need to stop the store from removing the
                                     * feature from the layer.
                                     */
                                    featureStore._removing = true; // TODO: remove after http://trac.geoext.org/ticket/141
                                    featureStore.remove(featureStore.getRecordFromFeature(feature));
                                    delete featureStore._removing; // TODO: remove after http://trac.geoext.org/ticket/141
                                }
                                featureStore.save();
                            },
                            "canceledit": function(popup, feature) {
                                featureStore.commitChanges();
                            },
                            scope: this
                        }
                    });
                    this.popup = popup;
                }
            },
            "sketchcomplete": function(evt) {
                // Why not register for featuresadded directly? We only want
                // to handle features here that were just added by a
                // DrawFeature control, and we need to make sure that our
                // featuresadded handler is executed after any FeatureStore's,
                // because otherwise our selectControl.select statement inside
                // this handler would trigger a featureselected event before
                // the feature row is added to a FeatureGrid. This, again,
                // would result in the new feature not being shown as selected
                // in the grid.
                featureManager.featureLayer.events.register("featuresadded", this, function(evt) {
                    featureManager.featureLayer.events.unregister("featuresadded", this, arguments.callee);
                    this.drawControl.deactivate();
                    this.selectControl.activate();
                    this.selectControl.select(evt.features[0]);
                });
            },
            scope: this
        });

        var toggleGroup = this.toggleGroup || Ext.id();

        var actions = [];
        var commonOptions = {
            tooltip: this.createFeatureActionTip,
            // backwards compatibility: only show text if configured
            menuText: this.initialConfig.createFeatureActionText,
            text: this.initialConfig.createFeatureActionText,
            iconCls: this.iconClsAdd,
            disabled: true,
            hidden: this.modifyOnly || this.readOnly,
            toggleGroup: toggleGroup,
            //TODO Tool.js sets group, but this doesn't work for GeoExt.Action
            group: toggleGroup,
            groupClass: null,
            enableToggle: true,
            allowDepress: true,
            control: this.drawControl,
            deactivateOnDisable: true,
            map: this.target.mapPanel.map,
            listeners: {checkchange: this.onItemCheckchange, scope: this}
        };
        if (this.supportAbstractGeometry === true) {
            var menuItems = [];
            if (this.supportNoGeometry === true) {
                menuItems.push(
                    new Ext.menu.CheckItem({
                        text: this.noGeometryText,
                        iconCls: "gxp-icon-event",
                        groupClass: null,
                        group: toggleGroup,
                        listeners: {
                            checkchange: function(item, checked) {
                                if (checked === true) {
                                    var feature = new OpenLayers.Feature.Vector(null);
                                    feature.state = OpenLayers.State.INSERT;
                                    featureLayer.addFeatures([feature]);
                                    this._forcePopupForNoGeometry = true;
                                    featureLayer.events.triggerEvent("featureselected", {feature: feature});
                                    delete this._forcePopupForNoGeometry;
                                }
                                if (this.createAction.items[0] instanceof Ext.menu.CheckItem) {
                                    this.createAction.items[0].setChecked(false);
                                } else {
                                    this.createAction.items[0].toggle(false);
                                }
                            },
                            scope: this
                        }
                    })
                );
            }
            var checkChange = function(item, checked, Handler) {
                if (checked === true) {
                    this.setHandler(Handler, false);
                }
                if (this.createAction.items[0] instanceof Ext.menu.CheckItem) {
                    this.createAction.items[0].setChecked(checked);
                } else {
                    this.createAction.items[0].toggle(checked);
                }
            };
            menuItems.push(
                new Ext.menu.CheckItem({
                    groupClass: null,
                    text: this.pointText,
                    group: toggleGroup,
                    iconCls: 'gxp-icon-point',
                    listeners: {
                        checkchange: checkChange.createDelegate(this, [OpenLayers.Handler.Point], 2)
                    }
                }),
                new Ext.menu.CheckItem({
                    groupClass: null,
                    text: this.lineText,
                    group: toggleGroup,
                    iconCls: 'gxp-icon-line',
                    listeners: {
                        checkchange: checkChange.createDelegate(this, [OpenLayers.Handler.Path], 2)
                    }
                }),
                new Ext.menu.CheckItem({
                    groupClass: null,
                    text: this.polygonText,
                    group: toggleGroup,
                    iconCls: 'gxp-icon-polygon',
                    listeners: {
                        checkchange: checkChange.createDelegate(this, [OpenLayers.Handler.Polygon], 2)
                    }
                })
            );

            actions.push(
                new GeoExt.Action(Ext.apply(commonOptions, {
                    menu: new Ext.menu.Menu({items: menuItems})
                }))
            );
        } else {
            actions.push(new GeoExt.Action(commonOptions));
        }
        actions.push(new GeoExt.Action({
            tooltip: this.editFeatureActionTip,
            // backwards compatibility: only show text if configured
            text: this.initialConfig.editFeatureActionText,
            menuText: this.initialConfig.editFeatureActionText,
            iconCls: this.iconClsEdit,
            disabled: true,
            toggleGroup: toggleGroup,
            //TODO Tool.js sets group, but this doesn't work for GeoExt.Action
            group: toggleGroup,
            groupClass: null,
            enableToggle: true,
            allowDepress: true,
            control: this.selectControl,
            deactivateOnDisable: true,
            map: this.target.mapPanel.map,
            listeners: {checkchange: this.onItemCheckchange, scope: this}
        }));
        
        this.createAction = actions[0];
        this.editAction = actions[1];
        
        if (this.splitButton) {
            this.splitButton = new Ext.SplitButton({
                menu: {items: [
                    Ext.apply(new Ext.menu.CheckItem(actions[0]), {
                        text: this.createFeatureActionText
                    }),
                    Ext.apply(new Ext.menu.CheckItem(actions[1]), {
                        text: this.editFeatureActionText
                    })
                ]},
                disabled: true,
                buttonText: this.splitButtonText,
                tooltip: this.splitButtonTooltip,
                iconCls: this.iconClsAdd,
                enableToggle: true,
                toggleGroup: this.toggleGroup,
                allowDepress: true,
                handler: function(button, event) {
                    if(button.pressed) {
                        button.menu.items.itemAt(this.activeIndex).setChecked(true);
                    }
                },
                scope: this,
                listeners: {
                    toggle: function(button, pressed) {
                        // toggleGroup should handle this
                        if(!pressed) {
                            button.menu.items.each(function(i) {
                                i.setChecked(false);
                            });
                        }
                    },
                    render: function(button) {
                        // toggleGroup should handle this
                        Ext.ButtonToggleMgr.register(button);
                    }
                }
            });
            actions = [this.splitButton];
        }

        actions = gxp.plugins.FeatureEditor.superclass.addActions.call(this, actions);

        featureManager.on("layerchange", this.onLayerChange, this);

        var snappingAgent = this.getSnappingAgent();
        if (snappingAgent) {
            snappingAgent.registerEditor(this);
        }

        return actions;
    },
    
    onItemCheckchange: function(item, checked) {
        if (this.splitButton) {
            this.activeIndex = item.ownerCt.items.indexOf(item);
            this.splitButton.toggle(checked);
            if (checked) {
                this.splitButton.setIconClass(item.iconCls);
            }
        }
    },

    /** private: method[getFeatureManager]
     *  :returns: :class:`gxp.plugins.FeatureManager`
     */
    getFeatureManager: function() {
        var manager = this.target.tools[this.featureManager];
        if (!manager) {
            throw new Error("Unable to access feature manager by id: " + this.featureManager);
        }
        return manager;
    },

    /** private: getSnappingAgent
     *  :returns: :class:`gxp.plugins.SnappingAgent`
     */
    getSnappingAgent: function() {
        var agent;
        var snapId = this.snappingAgent;
        if (snapId) {
            agent = this.target.tools[snapId];
            if (!agent) {
                throw new Error("Unable to locate snapping agent with id: " + snapId);
            }
        }
        return agent;
    },

    setHandler: function(Handler, multi) {
        var control = this.drawControl;
        var active = control.active;
        if(active) {
            control.deactivate();
        }
        control.handler.destroy(); 
        control.handler = new Handler(
            control, control.callbacks,
            Ext.apply(control.handlerOptions, {multi: multi})
        );
        if(active) {
            control.activate();
        } 
    },

    /**
     * private: method[enableOrDisable]
     */
    enableOrDisable: function() {
        // disable editing if no schema
        var disable = !this.schema;
        if (this.splitButton) {
            this.splitButton.setDisabled(disable);
        }
        this.createAction.setDisabled(disable);
        this.editAction.setDisabled(disable);
        return disable;
    },
    
    /** private: method[onLayerChange]
     *  :arg mgr: :class:`gxp.plugins.FeatureManager`
     *  :arg layer: ``GeoExt.data.LayerRecord``
     *  :arg schema: ``GeoExt.data.AttributeStore``
     */
    onLayerChange: function(mgr, layer, schema) {
        this.schema = schema;
        var disable = this.enableOrDisable();
        if (disable) {
            // not a wfs capable layer
            this.fireEvent("layereditable", this, layer, false);
            return;
        }

        var control = this.drawControl;
        var button = this.createAction;
        var handlers = {
            "Point": OpenLayers.Handler.Point,
            "Line": OpenLayers.Handler.Path,
            "Curve": OpenLayers.Handler.Path,
            "Polygon": OpenLayers.Handler.Polygon,
            "Surface": OpenLayers.Handler.Polygon
        };
        var simpleType = mgr.geometryType.replace("Multi", "");
        var Handler = handlers[simpleType];
        if (Handler) {
            var multi = (simpleType != mgr.geometryType);
            this.setHandler(Handler, multi);
            button.enable();
        } else if (this.supportAbstractGeometry === true && mgr.geometryType === 'Geometry') {
            button.enable();
        } else {
            button.disable();
        }
        this.fireEvent("layereditable", this, layer, true);
    },
    
    /** private: method[select]
     *  :arg feature: ``OpenLayers.Feature.Vector``
     */
    select: function(feature) {
        this.selectControl.unselectAll(
            this.popup && this.popup.editing && {except: this.popup.feature});
        this.selectControl.select(feature);
    }
});

Ext.preg(gxp.plugins.FeatureEditor.prototype.ptype, gxp.plugins.FeatureEditor);
