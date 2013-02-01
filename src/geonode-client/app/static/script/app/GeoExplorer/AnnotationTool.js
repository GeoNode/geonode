Ext.namespace("GeoExplorer.plugins");

GeoExplorer.plugins.AnnotationTool = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = app_notes */
    ptype: "app_annotation",

    errorTitle: "Error creating annotation",

    iconCls: "gxp-icon-note",

    notesText: "Notes",

    showNotesText: "Show notes",

    projection: "EPSG:4326",
    
    /** api: method[addActions]
     */
    addActions: function() {
    	var currentFeature = null;
        var layer = new OpenLayers.Layer.Vector('geo_annotation_layer', {
        	displayInLayerSwitcher: false,
        	projection: this.projection,
            strategies: [new OpenLayers.Strategy.BBOX({resFactor: 1, ratio: 1}), new OpenLayers.Strategy.Save()],
            protocol: new OpenLayers.Protocol.HTTP({
                url: "/annotations/" + this.target.mapID,
                format: new OpenLayers.Format.GeoJSON()
            })
        }); 

        var addPointControl = new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler['Point'], {'displayClass': 'olControlDrawFeaturePoint', 'title': 'Create Point Annotation'});
        var addPolygonControl = new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler['Polygon'], {'displayClass': 'olControlDrawFeaturePolygon', 'title': 'Create Polygon Annotation'});     
        var addLineControl = new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler['Path'], {'displayClass': 'olControlDrawFeaturePath', 'title': 'Create Line Annotation'});  
        var modControl = new OpenLayers.Control.ModifyFeature(layer, {vertexRenderIntent: 'temporary'});
        var selectAnnoControl = new OpenLayers.Control.SelectFeature(layer);
    	        
        
//        var contentField = new Ext.form.TextArea();
//        
//        var titleField = new Ext.form.TextField({
//            fieldLabel: "Title",
//            id: "popup_form_title",
//            value: "",
//        });
        
//        var saveButton = new Ext.Button({
//            id: 'anno_saveButton',
//            text: "Save",
//            cls:'x-btn-text',
//            style:"display:inline-block;",
//            handler: function(e) {
//                save_annotation();
//                return false;
//            },
//            scope: this
//        });
//        
//        var deleteButton = new Ext.Button({
//            id: 'anno_deleteButton',
//            text: "Delete",
//            cls:'x-btn-text',
//            style:"display:inline-block;",
//            handler: function(e) {
//            	currentFeature.state = OpenLayers.State.DELETE; 
//                save_annotation();
//                return false;
//            },
//            scope: this
//        });
        
        
//        var editPanel = new Ext.FormPanel(
//        	{
//        	xtype: "form",
//            bodyStyle: {padding: "5px"},
//            labelAlign: "top",
//            items: [
//
//            ],
//        	bbar: [
//                   saveButton,
//                   "->",
//                   deleteButton                	        
//       	    ]
//        });

        
        function featureSelected(evt) {
            var type = evt.feature.layer.name;
            var html = '<b>'+type+'</b><ul>';
            for (var key in evt.feature.attributes) {
                html += '<li><b>'+ key + '</b>: ' + evt.feature.attributes[key]+"</li>";
            }
            document.getElementById("featuredetails").innerHTML = html;
            
        	//modControl.selectFeature(evt.feature);
        	currentFeature = evt.feature;
            var pos = currentFeature.geometry;
            
            
            if (selectAnnoControl) {
                if (selectAnnoControl.popup) {
                	selectAnnoControl.popup.close();
                }
                
                newPanel = new Ext.Panel({
                    autoLoad: {
                    	url: "/annotations/" + currentFeature.fid + "/details", 
                    	scripts: true
                    }
                })
                
                selectAnnoControl.popup = new GeoExt.Popup({
                    title:currentFeature.attributes.title,
                    autoScroll: true,
                    height: 300,
                    listeners: {
                    	'close': function() {
                            modControl.unselectFeature(currentFeature);
                            currentFeature = null;
                    	}
                    },
                    location:currentFeature,
                    items: [newPanel]
                });
                selectAnnoControl.popup.show();        	
            }        	
        }
        
        function register() {
            this.events.register('featureadded', this, added);
            this.events.register('beforefeaturemodified', this, added);
            this.events.unregister('loadend', this, register);
        }
        
        
        function getForm() {
		        return {
   		        	xtype: "form",
   		        	bodyStyle: {padding: "5px"},
   		        	labelAlign: "top",
   		        	items: [
    	                   {
       	                    	   xtype: 'textfield',
       	                    	   fieldLabel: "Title",
       	                           id: "popup_form_title",
       	                           value: currentFeature && currentFeature.attributes["title"] ? currentFeature.attributes["title"]: "",
       	                   },
   	                       {
   	                    	   xtype: 'textarea',
   	                    	   width: 400,
   	                    	   height: 100,
   	                    	   fieldLabel: "Note",
   	                    	   id: "popup_form_content",
   	                    	   value: currentFeature && currentFeature.attributes["content"] ? currentFeature.attributes["content"]: "",
   	                       }
   		        	],
   		        	bbar: [
   	                       {
   	                    	   xtype: 'button',
   	                           id: 'anno_saveButton',
   	                           text: "Save",
   	                           cls:'x-btn-text',
   	                           style:"display:inline-block;",
   	                           handler: function(e) {
   	                               save_annotation();
   	                               return false;
   	                           },
   	                           scope: this
   	                       },
   	                       "->",
   	                       {
   	                    	   xtype: 'button',
   	                           id: 'anno_deleteButton',
   	                           text: "Cancel",
   	                           cls:'x-btn-text',
   	                           style:"display:inline-block;",
   	                           handler: function(e) {
   	                           	currentFeature.state = OpenLayers.State.DELETE; 
   	                               save_annotation();
   	                               return false;
   	                           },
   	                           scope: this
   	                       }                     	        
   		        	]
   		        };
        }
        
        function added(evt) {
           if (currentFeature && currentFeature.state == "Insert" && currentFeature != evt.feature) {
                layer.removeFeatures(currentFeature);
            }   
            //displayForm(evt.feature);
           currentFeature = evt.feature;
           if (modControl) {
               if (modControl.popup) {
            	   modControl.popup.close();
               }
               modControl.popup = new GeoExt.Popup({
                   title:"New Note",
                   width: 450,
                   listeners: {
                   	'beforeclose': function() {
                           modControl.unselectFeature(currentFeature);
                           currentFeature = null;
                   	}
                   },
                   location:evt.feature,
               	   items: [getForm()]
               });
               modControl.popup.show(); 
               
           }
        }

        function displayForm(feature) {
            currentFeature = feature;
            var form = 'data_form';
            var formdom = document.forms['data_form'];
            for (var i = 0; i < formdom.length; i++) {
                if (formdom[i].type == "submit") {continue;}
                if (currentFeature.attributes[formdom[i].name] != undefined) {
                    formdom[i].value = currentFeature.attributes[formdom[i].name] || "";
                } else {
                    formdom[i].value = "";
                }    
            }            
        }    
        
        function save_annotation() {
        	currentFeature.attributes["title"] = Ext.getCmp("popup_form_title").getValue();
        	currentFeature.attributes["content"] = Ext.getCmp("popup_form_content").getValue();        	
            layer.strategies[1].save([currentFeature]);
            modControl.unselectFeature(currentFeature);
            currentFeature = null;
            if (modControl.popup) {
         	   modControl.popup.close();
            }
            
        }

        layer.events.register('loadend', layer, register);
        layer.events.register('featureselected', this, featureSelected);
        
        AnnoAddToolbar = OpenLayers.Class(OpenLayers.Control.Panel, {	
            initialize: function(options) {
                OpenLayers.Control.Panel.prototype.initialize.apply(this, [options]);
                this.defaultControl = selectAnnoControl;
                    this.addControls( [
                        addPointControl, addLineControl,addPolygonControl
                    ]);                   
                    this.displayClass = 'myToolbar';
                
            },
            CLASS_NAME: 'AnnoAddToolbar'
        });

        var add_toolbar = new AnnoAddToolbar();      
        this.target.mapPanel.map.addControl(add_toolbar);
        this.target.mapPanel.map.addControls([modControl,selectAnnoControl]); 

        
        return GeoExplorer.plugins.AnnotationTool.superclass.addActions.apply(this, [{
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
                            checkchange: function(item, checked) {
                                if (checked === true) {
                                    this.target.mapPanel.map.addLayer(layer);
                                    selectAnnoControl.activate();
                                } else {
                                	this.target.mapPanel.map.removeLayer(layer);
                                	selectAnnoControl.deactivate();
                                }
                            },
                            scope: this
                        }
                    }),
                    new Ext.menu.CheckItem({
                        checked: false,
                        text: "Add Notes",
                        listeners: {
                            checkchange: function(item, checked) {
                                if (checked === true) {
                                	Ext.getCmp("check_view_annotations").setChecked(true);
                                	add_toolbar.activate();
                                	selectAnnoControl.deactivate();
                                } else {
                                	add_toolbar.deactivate();    
                                	selectAnnoControl.activate();
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