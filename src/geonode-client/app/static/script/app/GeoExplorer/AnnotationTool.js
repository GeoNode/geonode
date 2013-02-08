Ext.namespace("GeoExplorer.plugins");


GeoExplorer.plugins.AnnotationTool = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = app_notes */
    ptype: "app_annotation",

    errorTitle: "Error creating annotation",

    iconCls: "gxp-icon-note",

    notesText: "Notes",

    showNotesText: "Show notes",
    
    editNotesText: "Edit notes",

    projection: "EPSG:4326",

    pointText: "Point",

    lineText: "Line",

    polygonText: "Shape",

    /**
     * api: method[addActions]
     */
    addActions: function () {
        var currentFeature = null;
        var layer = new OpenLayers.Layer.Vector(
            'geo_annotation_layer', {
            displayInLayerSwitcher: false,
            projection: this.projection,
            strategies: [
            new OpenLayers.Strategy.BBOX(),
            new OpenLayers.Strategy.Save()],
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
        layer, {selectStyle: "olHandlerBoxSelectFeature"});


        function checkAddChange(checkbox) {
            if (!checkbox.checked) {
                addPointControl.deactivate();
                addLineControl.deactivate();
                addPolygonControl.deactivate();
            } else {
                Ext.getCmp("check_view_annotations").setChecked(
                true);
            }
        }

        function checkToolChange(checkbox) {
            addPointControl.deactivate();
            addLineControl.deactivate();
            addPolygonControl.deactivate();
            Ext.getCmp("check_view_annotations").setChecked(
            true);
            Ext.getCmp("check_add_annotations").setChecked(
            true);
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

        function featureSelected(evt) {
            if (currentFeature && currentFeature != evt.feature) {
            	selectAnnoControl.unhighlight(currentFeature);
            }

            if (Ext.getCmp("check_edit_annotations").checked) {
            	added(evt);
            	return false;
            }
            
            
            
            var type = evt.feature.layer.name;
            var html = '<b>' + type + '</b><ul>';
            for (var key in evt.feature.attributes) {
                html += '<li><b>' + key + '</b>: ' + evt.feature.attributes[key] + "</li>";
            }
            document.getElementById("featuredetails").innerHTML = html;

            // modControl.selectFeature(evt.feature);

            var pos = evt.feature.geometry;

            if (selectAnnoControl) {
//                if (selectAnnoControl.popup) {
//                    selectAnnoControl.popup.close();
//                }

                var newPanel = new Ext.Panel({
                    autoLoad: {
                        url: "/annotations/" + evt.feature.fid + "/details",
                        scripts: true
                    }
                })
                currentFeature = evt.feature;
                selectAnnoControl.highlight(evt.feature);
                var popup = new GeoExt.Popup({
                    title: evt.feature.attributes.title,
                    closeAction: "close",
                    autoScroll: true,
                    height: 300,
                    listeners: {
                        'beforeclose': function () {
                            selectAnnoControl.unhighlight(evt.feature);
                            evt.feature = null;
                            currentFeature = null;
                        }
                    },
                    location: evt.feature,
                    items: [newPanel]
                });
                popup.show();
            }
        }

        
        
        function register() {
            this.events.register('featureadded', this, added);
            this.events.register('beforefeaturemodified', this,
            added);
            this.events.unregister('loadend', this, register);
        }

        function getForm() {
            return {
                xtype: "form",
                bodyStyle: {
                    padding: "5px"
                },
                labelAlign: "top",
                items: [{
                    xtype: 'textfield',
                    fieldLabel: "Title",
                    id: "popup_form_title",
                    value: currentFeature && currentFeature.attributes["title"] ? currentFeature.attributes["title"] : ""
                }, {
                    xtype: 'textarea',
                    width: 400,
                    height: 100,
                    fieldLabel: "Note",
                    id: "popup_form_content",
                    value: currentFeature && currentFeature.attributes["content"] ? currentFeature.attributes["content"] : ""
                }],
                bbar: [{
                    xtype: 'button',
                    id: 'anno_saveButton',
                    text: "Save",
                    cls: 'x-btn-text',
                    style: "display:inline-block;",
                    handler: function (e) {
                        save_annotation();
                        return false;
                    },
                    scope: this
                },
                    "->", {
                    xtype: 'button',
                    id: 'anno_deleteButton',
                    text: "Delete",
                    cls: 'x-btn-text',
                    style: "display:inline-block;",
                    handler: function (e) {
                    	if (currentFeature.fid) {
                    		currentFeature.state = OpenLayers.State.DELETE;
                    		save_annotation();
                    	} else {
                    		modControl.popup.close();
                    	}
                        return false;
                    },
                    scope: this
                }]
            };
        }

        function added(evt) {
//            if (currentFeature != evt.feature) {
//                layer.removeFeatures(currentFeature);
//            }
//            if (!evt.feature.fid) {
                // displayForm(evt.feature);
                currentFeature = evt.feature;                
                if (modControl) {
                    if (modControl.popup) {
                        modControl.popup.close();
                    }
                    modControl.popup = new GeoExt.Popup({
                        title: "New Note",
                        width: 450,
                        closeAction: "close",
                        listeners: {
                            'beforeclose': function () {
                                modControl.unselectFeature(currentFeature);
                                if (currentFeature && !currentFeature.fid) {
                                	layer.removeFeatures(currentFeature);
                                }
                            }
                        },
                        location: evt.feature,
                        items: [getForm()]
                    });
                    modControl.popup.show();

                }
//            } else if (modControl && modControl.popup) {
//                modControl.popup.close();
//            }
        }

        function displayForm(feature) {
            currentFeature = feature;
            var form = 'data_form';
            var formdom = document.forms['data_form'];
            for (var i = 0; i < formdom.length; i++) {
                if (formdom[i].type == "submit") {
                    continue;
                }
                if (currentFeature.attributes[formdom[i].name] != undefined) {
                    formdom[i].value = currentFeature.attributes[formdom[i].name] || "";
                } else {
                    formdom[i].value = "";
                }
            }
        }

        function save_annotation() {
            currentFeature.attributes["title"] = Ext.getCmp(
                "popup_form_title").getValue();
            currentFeature.attributes["content"] = Ext.getCmp(
                "popup_form_content").getValue();
            layer.strategies[1].save([currentFeature]);
            currentFeature = null;
            if (modControl.popup) {
                modControl.popup.close();
            }

        }

        layer.events.register('loadend', layer, register);
        layer.events.register('featureselected', this, featureSelected);

        this.target.mapPanel.map.addControls([modControl,
         addPointControl,addLineControl, addPolygonControl]);

        return GeoExplorer.plugins.AnnotationTool.superclass.addActions.apply(
        this, [{
            text: this.notesText,
            disabled: !this.target.mapID,
            iconCls: this.iconCls,
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
                                this.target.mapPanel.map.addLayer(layer);
                                selectAnnoControl.activate();
                            } else {
                                this.target.mapPanel.map.removeLayer(layer);
                                selectAnnoControl.deactivate();
                                Ext.getCmp("check_add_annotations").setChecked(
                                false);

                            }
                        },
                        scope: this
                    }
                }),
                new Ext.menu.CheckItem({
                    id: "check_add_annotations",
                    checked: false,
                    listeners: {
                        checkchange: checkAddChange,
                        scope: this
                    },
                    text: "Add Note",
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
                    })]
                }),
                new Ext.menu.CheckItem({
                    id: "check_edit_annotations",
                    checked: false,
                    text: this.editNotesText,
                    listeners: {
                        checkchange: function (
                        item,
                        checked) {
                            if (checked === true) {
                                Ext.getCmp("check_view_annotations").setChecked(
                                        true);
                                Ext.getCmp("check_add_annotations").setChecked(
                                        false);
//                                this.target.mapPanel.map.addLayer(layer);
//                                addPointControl.deactivate();
//                                addLineControl.deactivate();
//                                addPolygonControl.deactivate();
                                selectAnnoControl.activate();
                                modControl.activate();
                            } else {
                                modControl.deactivate();
                            }
                        },
                        scope: this
                    }
                })
                ]
            })
        }]);
    }

});

Ext.preg(GeoExplorer.plugins.AnnotationTool.prototype.ptype, GeoExplorer.plugins.AnnotationTool);