Ext.namespace("gxp.plugins");

gxp.plugins.AnnotationTool = Ext.extend(gxp.plugins.Tool, {
    /** api: ptype = gxp_annotation */
    ptype: "gxp_annotation",
    
    iconCls: "gxp-icon-note",
    
    currentFeature: null,
    
    errorTitle: "Error creating annotation",

    noteText: "Note",
    
    notesText: "Notes",

    showNotesText: "Show notes",

    editNotesText: "Edit notes",
    
    addNoteText: "Add note",
    
    newNoteText: "New note",

    projection: "EPSG:4326",

    pointText: "Point",

    lineText: "Line",

    polygonText: "Shape",

    saveFailTitle: "Could not save note",

    saveFailText: "Edit failed.  You might not have permission to save this note.",
    
    saveText: "Save",
    
    editText: "Edit",
    
    deleteText: "Delete",
    
    cancelText: "Cancel",
    
    titleText: "Title",
    
    

    /**
     * api: method[addActions]
     */
    addActions: function () {

        function saveFail(evt) {
            Ext.Msg.alert(this.saveFailTitle,
                    this.saveFailText);
        }

        var saveStrategy = new OpenLayers.Strategy.Save();
        saveStrategy.events.register('fail', this, saveFail);

        var currentUser = this.user;
		var isMapEditor = this.target.config["edit_map"];
		
        var layer = new OpenLayers.Layer.Vector(
            'geo_annotation_layer', {
                displayInLayerSwitcher: false,
                projection: this.projection,
                strategies: [
                    new OpenLayers.Strategy.BBOX(),
                    saveStrategy
                ],
                protocol: new OpenLayers.Protocol.HTTP({
                    url: "/annotations/" + this.target.mapID,
                    format: new OpenLayers.Format.GeoJSON()
                })
            });

        var addPointControl = new OpenLayers.Control.DrawFeature(
            layer,
            OpenLayers.Handler['Point'], {
                'displayClass': 'olControlDrawFeaturePoint',
                'title': 'Create Point Annotation'
            });
        var addPolygonControl = new OpenLayers.Control.DrawFeature(
            layer,
            OpenLayers.Handler['Polygon'], {
                'displayClass': 'olControlDrawFeaturePolygon',
                'title': 'Create Polygon Annotation'
            });
        var addLineControl = new OpenLayers.Control.DrawFeature(
            layer,
            OpenLayers.Handler['Path'], {
                'displayClass': 'olControlDrawFeaturePath',
                'title': 'Create Line Annotation'
            });
        var modControl = new OpenLayers.Control.ModifyFeature(
            layer, {
                vertexRenderIntent: 'temporary'
            });
        var selectAnnoControl = new OpenLayers.LayerFeatureAgent(
            layer, {
                renderIntent: "select"
            });

        function checkAddChange(checkbox) {
            if (!checkbox.checked) {
                addPointControl.deactivate();
                addLineControl.deactivate();
                addPolygonControl.deactivate();
            } else {
                Ext.getCmp("check_view_annotations")
                    .setChecked(true);
            }
        }

        function checkToolChange(checkbox) {
            addPointControl.deactivate();
            addLineControl.deactivate();
            addPolygonControl.deactivate();
            Ext.getCmp("check_view_annotations").setChecked(
                true);
            Ext.getCmp("check_add_annotations")
                .setChecked(true);
            switch (checkbox.text) {
            case this.pointText:
                addPointControl.activate();
                break;
            case this.lineText:
                addLineControl.activate();
                break;
            case this.polygonText:
                addPolygonControl.activate();
                break;
            default:
                break;
            }
        }

        function multipleSelected(evt) {
            var items = [];
            var multiplePopup = null;

            for (var f = 0; f < evt.features.length; f++) {
                var feature = evt.features[f];

                items.push({
                    xtype: 'button',
                    text: "" + f + " " + feature.attributes.title,
                    feature: feature,
                    cls: 'x-btn-text',
                    handler: function (e) {
                        featureSelected(e);
                        multiplePopup.close();
                        return false;
                    },
                    scope: this
                });
            }

            multiplePopup = new GeoExt.Popup({
                title: "Select Note",
                closeAction: "close",
                autoScroll: true,
                location: evt.features[0],
                items: [items]
            });
            multiplePopup.show();

        }

        function featureSelected(evt) {
            if (this.currentFeature && this.currentFeature != evt.feature) {
                selectAnnoControl
                    .unhighlight(this.currentFeature);
            }

            if (selectAnnoControl) {
                if (selectAnnoControl.popup) {
                    selectAnnoControl.popup.close();
                }

                var newPanel = new Ext.Panel({
                    autoLoad: {
                        url: "/annotations/" + evt.feature.fid + "/details",
                        scripts: true
                    }
                });
                this.currentFeature = evt.feature;
                selectAnnoControl
                    .highlight(this.currentFeature);
                selectAnnoControl.popup = new GeoExt.Popup({
                    title: evt.feature.attributes.title,
                    closeAction: "close",
                    autoScroll: true,
                    height: 300,
                    width: 400,
                    listeners: {
                        'beforeclose': function () {
                            selectAnnoControl
                                .unhighlight(evt.feature);
                            evt.feature = null;
                            this.currentFeature = null;
                        }
                    },
                    location: evt.feature,
                    items: [newPanel],
                    bbar: [{
                            xtype: 'button',
                            id: 'anno_editButton',
                            text: this.editText,
                            disabled: currentUser != this.currentFeature.attributes["owner_id"] && !isMapEditor,
                            cls: 'x-btn-text',
                            style: "display:inline-block;",
                            handler: function (e) {
                                addEditNote.call(this, evt);
                                selectAnnoControl.popup.close();
                                return false;
                            },
                            scope: this
                        },
                        "->", {
                            xtype: 'button',
                            id: 'anno_deleteButton',
                            disabled: currentUser != this.currentFeature.attributes["owner_id"] && !isMapEditor,
                            text: this.deleteText,
                            cls: 'x-btn-text',
                            style: "display:inline-block;",
                            handler: function (e) {
                                this.currentFeature.state = OpenLayers.State.DELETE;
                                save_annotation.call(this);
                                selectAnnoControl.popup.close();
                                return false;
                            },
                            scope: this
                        }
                    ]
                });
                selectAnnoControl.popup.show();
            }
        }

        function added(evt) {
            if (!evt.feature.fid) {
                addEditNote.call(this, evt);
            }
        }

        function cancelEdit() {
            modControl.unselectFeature(this.currentFeature);
            if (!this.currentFeature.saved) {
                layer.refresh({
                    force: true
                });
            }
            modControl.deactivate();
            selectAnnoControl.activate();
            selectAnnoControl.unhighlight(this.currentFeature);
        }

        function addEditNote(evt) {
            selectAnnoControl.deactivate();
            this.currentFeature = evt.feature;
            this.currentFeature.saved = false;

            if (modControl) {
                modControl.activate();
                modControl.selectFeature(this.currentFeature);
                if (!this.currentFeature.state)
                    this.currentFeature.state = OpenLayers.State.UPDATE;
                if (modControl.popup) {
                    modControl.popup.close();
                }
                modControl.popup = new GeoExt.Popup({
                    title: this.newNoteText,
                    width: 450,
                    closeAction: "close",
                    listeners: {
                        'beforeclose': cancelEdit,
                        scope: this
                    },
                    scope: this,
                    location: evt.feature,
                    items: [{
                        xtype: "form",
                        bodyStyle: {
                            padding: "5px"
                        },
                        labelAlign: "top",
                        items: [{
                            xtype: 'textfield',
                            fieldLabel: this.titleText,
                            id: "popup_form_title",
                            value: this.currentFeature && this.currentFeature.attributes["title"] ? this.currentFeature.attributes["title"] : ""
                        }, {
                            xtype: 'textarea',
                            width: 400,
                            height: 100,
                            fieldLabel: this.noteText,
                            id: "popup_form_content",
                            value: this.currentFeature && this.currentFeature.attributes["content"] ? this.currentFeature.attributes["content"] : ""
                        }]
                    }],
                    bbar: [{
                            xtype: 'button',
                            id: 'anno_saveButton',
                            text: this.saveText,
                            cls: 'x-btn-text',
                            style: "display:inline-block;",
                            handler: function (e) {
                                save_annotation.call(this);
                                return false;
                            },
                            scope: this
                        },
                        "->", {
                            xtype: 'button',
                            id: 'anno_cancelButton',
                            text: this.cancelText,
                            cls: 'x-btn-text',
                            style: "display:inline-block;",
                            handler: function (e) {
                                modControl.popup.close();
                                return false;
                            },
                            scope: this
                        }
                    ]
                });
                modControl.popup.show();

            }
        }

        function save_annotation() {
            if (this.currentFeature.state != OpenLayers.State.DELETE) {
                this.currentFeature.attributes["title"] = Ext
                    .getCmp("popup_form_title").getValue();
                this.currentFeature.attributes["content"] = Ext
                    .getCmp("popup_form_content").getValue();
            }
            layer.strategies[1].save([this.currentFeature]);
            this.currentFeature.saved = true;
            modControl.unselectFeature(this.currentFeature);
            if (!this.currentFeature.attributes["owner_id"]) {
                this.currentFeature.attributes["owner_id"] = currentUser;
            }

            if (modControl.popup) {
                modControl.popup.close();
            }

        }

        return gxp.plugins.AnnotationTool.superclass.addActions.apply(
            this, [{
            text: this.notesText,
            disabled: !this.target.mapID,
            iconCls: this.iconCls,
            toggleGroup: this.toggleGroup,
            enableToggle: true,
            allowDepress: false,
            toggleHandler: function (button,
                pressed) {
                if (!pressed) {
                    Ext.getCmp("check_view_annotations").setChecked(false);
                }
            },
            menu: new Ext.menu.Menu({
                items: [
                    new Ext.menu.CheckItem({
                        id: "check_view_annotations",
                        checked: false,
                        text: this.showNotesText,
                        listeners: {
                            checkchange: function (
                                item,
                                checked) {
                                if (checked === true) {
                                    if (this.target.selectControl) {
                                        this.target.selectControl.deactivate();
                                    }
                                    this.target.mapPanel.map
                                        .addControls([
                                            modControl,
                                            addPointControl,
                                            addLineControl,
                                            addPolygonControl
                                        ]);
                                    this.target.mapPanel.map.addLayer(layer);
                                    selectAnnoControl.activate();
                                    layer.events.register('featureadded',this,added);
                                    layer.events .register('beforefeaturemodified',this, added);
                                    layer.events.register('featureselected',this,featureSelected);
                                    layer.events.register('multipleselected',this,multipleSelected);
                                } else {
                                    selectAnnoControl.deactivate();
                                    if (this.target.selectControl) {
                                        this.target.selectControl.activate();
                                    }
                                    this.target.mapPanel.map.removeLayer(layer);
                                    Ext.getCmp("check_add_annotations").setChecked(false);
                                    layer.events.unregister('multipleselected',this,multipleSelected);
                                    layer.events.unregister('featureselected',this,featureSelected);
                                    layer.events.unregister('featureadded',this,added);
                                    layer.events.unregister('beforefeaturemodified',this,added);

                                    var controls = new Array(
                                        modControl,
                                        addPointControl,
                                        addLineControl,
                                        addPolygonControl);

                                    for (var control = 0; control < controls.length; control++) {
                                        controls[control].deactivate();
                                        this.target.mapPanel.map.removeControl(controls[control]);
                                    }
                                }
                            },
                            scope: this
                        }
                    }),
                    new Ext.menu.CheckItem({
                        id: "check_add_annotations",
                        checked: false,
                        disabled: currentUser == "None",
                        listeners: {
                            checkchange: checkAddChange,
                            scope: this
                        },
                        text: this.addNoteText,
                        menu: [
                            new Ext.menu.CheckItem({
                                groupClass: null,
                                text: this.pointText,
                                group: 'featureeditorgroup',
                                iconCls: 'gxp-icon-point',
                                listeners: {
                                    click: checkToolChange,
                                    scope: this
                                }
                            }),
                            new Ext.menu.CheckItem({
                                groupClass: null,
                                text: this.lineText,
                                group: 'featureeditorgroup',
                                iconCls: 'gxp-icon-line',
                                listeners: {
                                    click: checkToolChange,
                                    scope: this
                                }
                            }),
                            new Ext.menu.CheckItem({
                                groupClass: null,
                                text: this.polygonText,
                                group: 'featureeditorgroup',
                                iconCls: 'gxp-icon-polygon',
                                        listeners: {
                                            click: checkToolChange,
                                            scope: this
                                        }
                                    })
                                ]
                            })
                        ]
                    })
                }]
            );
        }
});

Ext.preg(gxp.plugins.AnnotationTool.prototype.ptype,gxp.plugins.AnnotationTool);