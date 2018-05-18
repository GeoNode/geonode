/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp
 *  class = LayerUploadPanel
 *  base_link = `Ext.FormPanel <http://extjs.com/deploy/dev/docs/?class=Ext.FormPanel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: LayerUploadPanel(config)
 *   
 *      A panel for uploading new layer data to GeoServer.
 */
gxp.LayerUploadPanel = Ext.extend(Ext.FormPanel, {
    
    /** i18n */
    titleLabel: "Title",
    titleEmptyText: "Layer title",
    abstractLabel: "Description",
    abstractEmptyText: "Layer description",
    fileLabel: "Data",
    fieldEmptyText: "Browse for data archive...",
    uploadText: "Upload",
    waitMsgText: "Uploading your data...",
    invalidFileExtensionText: "File extension must be one of: ",
    optionsText: "Options",
    workspaceLabel: "Workspace",
    workspaceEmptyText: "Default workspace",
    dataStoreLabel: "Store",
    dataStoreEmptyText: "Create new store",
    defaultDataStoreEmptyText: "Default data store",
    crsLabel: "CRS",
    crsEmptyText: "Coordinate Reference System ID",
    invalidCrsText: "CRS identifier should be an EPSG code (e.g. EPSG:4326)",
    
    /** private: property[fileUpload]
     *  ``Boolean``
     */
    fileUpload: true,
    
    /** api: config[validFileExtensions]
     *  ``Array``
     *  List of valid file extensions.  These will be used in validating the 
     *  file input value.  Default is ``[".zip", ".tif", ".tiff", ".gz", ".tar.bz2", 
     *  ".tar", ".tgz", ".tbz2"]``.
     */
    validFileExtensions: [".zip", ".tif", ".tiff", ".gz", ".tar.bz2", ".tar", ".tgz", ".tbz2"],
    
    /** api: config[url]
     *  ``String``
     *  URL for GeoServer RESTConfig root.  E.g. "http://example.com/geoserver/rest".
     */
    
    /** private: property[defaultDataStore]
     *  ``string``
     */
    defaultDataStore: null,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        // Allow for a custom method to handle upload responses.
        config.errorReader = {
            read: config.handleUploadResponse || this.handleUploadResponse.createDelegate(this)
        };
        gxp.LayerUploadPanel.superclass.constructor.call(this, config);
    },
    
    /** private: property[selectedWorkspace]
     *  {Ext.data.Record}
     */
    selectedWorkspace: null,
    
    /** private: method[initComponent]
     */
    initComponent: function() {
        
        this.items = [{
            xtype: "textfield",
            name: "title",
            fieldLabel: this.titleLabel,
            emptyText: this.titleEmptyText,
            allowBlank: true
        }, {
            xtype: "textarea",
            name: "abstract",
            fieldLabel: this.abstractLabel,
            emptyText: this.abstractEmptyText,
            allowBlank: true
        }, {
            xtype: "fileuploadfield",
            id: "file",
            emptyText: this.fieldEmptyText,
            fieldLabel: this.fileLabel,
            name: "file",
            buttonText: "",
            buttonCfg: {
                iconCls: "gxp-icon-filebrowse"
            },
            listeners: {
                "fileselected": function(cmp, value) {
                    // remove the path from the filename - avoids C:/fakepath etc.
                    cmp.setValue(value.split(/[/\\]/).pop());
                }
            },
            validator: this.fileNameValidator.createDelegate(this)
        }, {
            xtype: "fieldset",
            title: this.optionsText,
            checkboxToggle: true,
            collapsed: true,
            hidden: this.workspace != undefined && this.store != undefined && this.crs != undefined,
            hideMode: "offsets",
            defaults: {
                anchor: "97%"
            },
            items: [
                this.createWorkspacesCombo(),
                this.createDataStoresCombo(),
                {
                    xtype: "textfield",
                    name: "nativeCRS",
                    // anchor: "90%",
                    fieldLabel: this.crsLabel,
                    emptyText: this.crsEmptyText,
                    allowBlank: true,
                    regex: /^epsg:\d+$/i,
                    regexText: this.invalidCrsText
                }
            ],
            listeners: {
                collapse: function(fieldset) {
                    // reset all combos
                    fieldset.items.each(function(item) {
                        item.reset();
                    });
                }
            }
        }];
        
        this.buttons = [{
            text: this.uploadText,
            handler: function() {
                var form = this.getForm();
                if (form.isValid()) {
                    var fields = form.getFieldValues(),
                        jsonData = {'import': {}};
                    if (fields.workspace) {
                        jsonData["import"].targetWorkspace = {workspace: {name: fields.workspace}};
                    }
                    if (fields.store) {
                        jsonData["import"].targetStore = {dataStore: {name: fields.store}}
                    } else if (this.defaultDataStore) {
                        jsonData["import"].targetStore = {dataStore: {name: this.defaultDataStore}}                        
                    }
                    Ext.Ajax.request({
                        url: this.getUploadUrl(),
                        method: "POST",
                        jsonData: jsonData,
                        success: function(response) {
                            this._import = response.getResponseHeader("Location");
                            form.submit({
                                url: this._import + "/tasks",
                                waitMsg: this.waitMsgText,
                                waitMsgTarget: true,
                                reset: true,
                                scope: this
                            });
                        },
                        scope: this
                    });
                }
            },
            scope: this
        }];
        
        this.addEvents(
            /**
             * Event: workspaceselected
             * Fires when a workspace is selected.
             *
             * Listener arguments:
             * panel - {<gxp.LayerUploadPanel} This form panel.
             * record - {Ext.data.Record} The selected workspace record.
             */
            "workspaceselected",

            /**
             * Event: datastoreselected
             * Fires when a datastore is selected.
             *
             * Listener arguments:
             * panel - {<gxp.LayerUploadPanel} This form panel.
             * record - {Ext.data.Record} The selected datastore record.
             */
            "datastoreselected",

            /**
             * Event: uploadcomplete
             * Fires upon successful upload.
             *
             * Listener arguments:
             * panel - {<gxp.LayerUploadPanel} This form panel.
             * details - {Object} An object with an "import" property,
             *     representing a summary of the import result as provided by
             *     GeoServer's Importer API.
             */
            "uploadcomplete"
        );
        
        this.getDefaultDataStore('default');

        gxp.LayerUploadPanel.superclass.initComponent.call(this);

    },
    
    /** private: method[fileNameValidator]
     *  :arg name: ``String`` The chosen filename.
     *  :returns: ``Boolean | String``  True if valid, message otherwise.
     */
    fileNameValidator: function(name) {
        var valid = false;
        var ext, len = name.length;
        for (var i=0, ii=this.validFileExtensions.length; i<ii; ++i) {
            ext = this.validFileExtensions[i];
            if (name.slice(-ext.length).toLowerCase() === ext) {
                valid = true;
                break;
            }
        }
        return valid || this.invalidFileExtensionText + '<br/>' + this.validFileExtensions.join(", ");
    },

    /** private: method[createWorkspacesCombo]
     *  :returns: ``Object`` Combo config.
     */
    createWorkspacesCombo: function() {
        return {
            xtype: "combo",
            name: "workspace",
            ref: "../workspace",
            fieldLabel: this.workspaceLabel,
            emptyText: this.workspaceEmptyText,
            store: new Ext.data.JsonStore({
                url: this.getWorkspacesUrl(),
                autoLoad: true,
                root: "workspaces.workspace",
                fields: ["name", "href"]
            }),
            displayField: "name",
            valueField: "name",
            mode: "local",
            allowBlank: true,
            triggerAction: "all",
            editable: false,
            listeners: {
                select: function(combo, record, index) {
                    this.getDefaultDataStore(record.get('name'));
                    this.fireEvent("workspaceselected", this, record);
                },
                scope: this
            }
        };
    },
    
    /** private: method[createDataStoresCombo]
     *  :returns: ``Ext.form.ComboBox``
     */
    createDataStoresCombo: function() {
        // this store will be loaded whenever a workspace is selected
        var store = new Ext.data.JsonStore({
            autoLoad: false,
            root: "dataStores.dataStore",
            fields: ["name", "href"]
        });
        this.on({
            workspaceselected: function(panel, record) {
                combo.reset();
                var workspaceUrl = record.get("href");
                store.removeAll();
                store.proxy = new Ext.data.HttpProxy({
                    url: workspaceUrl.split(".json").shift() + "/datastores.json"
                });
                store.load();
            },
            scope: this
        });

        var combo = new Ext.form.ComboBox({
            name: "store",
            ref: "../dataStore",
            fieldLabel: this.dataStoreLabel,
            emptyText: this.dataStoreEmptyText,
            store: store,
            displayField: "name",
            valueField: "name",
            mode: "local",
            allowBlank: true,
            triggerAction: "all",
            editable: false,
            listeners: {
                select: function(combo, record, index) {
                    this.fireEvent("datastoreselected", this, record);
                },
                scope: this
            }
        });
        
        return combo;
    },

    getDefaultDataStore: function(workspace) {
        Ext.Ajax.request({
            url: this.url + '/workspaces/' + workspace + '/datastores/default.json',
            callback: function(options, success, response) {
                this.defaultDataStore = null;
                this.dataStore.emptyText = this.dataStoreEmptyText;
                this.dataStore.setValue('');
                if (response.status === 200) {
                    var json = Ext.decode(response.responseText);
                    //TODO Revisit this logic - currently we assume that stores
                    // with the substring "file" in the type are file based,
                    // and for file-based data stores we want to crate a new
                    // store.
                    if (json.dataStore && json.dataStore.enabled === true && !/file/i.test(json.dataStore.type)) {
                        this.defaultDataStore = json.dataStore.name;
                        this.dataStore.emptyText = this.defaultDataStoreEmptyText;
                        this.dataStore.setValue('');
                    }
                }
            },
            scope: this
        });
    },

    /** private: method[getUploadUrl]
     */
    getUploadUrl: function() {
        return this.url + "/imports";
    },
    
    /** private: method[getWorkspacesUrl]
     */
    getWorkspacesUrl: function() {
        return this.url + "/workspaces.json";
    },
    
    /** private: method[handleUploadResponse]
     *  TODO: if response includes errors object, this can be removed
     *  Though it should only be removed if the server always returns text/html!
     */
    handleUploadResponse: function(response) {
        var obj = this.parseResponseText(response.responseText),
            records, tasks, task, msg, i,
            success = true;
        if (obj) {
            tasks = obj.tasks || [obj.task];
            for (i=tasks.length-1; i>=0; --i) {
                task = tasks[i];
                if (task.state !== "READY") {
                    success = false;
                    msg = "Source " + task.source.file + " is " + task.state;
                    break;
                }
            }
        }
        if (!success) {
            // mark the file field as invlid
            records = [{data: {id: "file", msg: msg}}];
        } else {
            var formData = this.getForm().getFieldValues(),
                // for now we only support a single item (items[0])
                resource = task.items[0].resource,
                itemModified = !!(formData.title || formData["abstract"] || formData.nativeCRS),
                queue = [];
            if (itemModified) {
                var layer = resource.featureType ? "featureType" : "coverage",
                    item = {resource: {}};
                item.resource[layer] = {
                    title: formData.title || undefined,
                    "abstract": formData["abstract"] || undefined,
                    nativeCRS: formData.nativeCRS || undefined
                };
                Ext.Ajax.request({
                    method: "PUT",
                    url: tasks[0].items[0].href,
                    jsonData: {item: item},
                    callback: this.finishUpload,
                    scope: this
                });
            } else {
                this.finishUpload();
            }
        }
        return {success: success, records: records};
    },
    
    finishUpload: function() {
        Ext.Ajax.request({
            method: "POST",
            url: this._import,
            //TODO error handling
            success: this.handleUploadSuccess,
            scope: this
        });
    },
    
    /** private: parseResponseText
     *  :arg text: ``String``
     *  :returns:  ``Object``
     *
     *  Parse the response text.  Assuming a JSON string but allowing for a 
     *  string wrapped in a <pre> element (given non text/html response type).
     */
    parseResponseText: function(text) {
        var obj;
        try {
            obj = Ext.decode(text);
        } catch (err) {
            // if response type was text/plain, the text will be wrapped in a <pre>
            var match = text.match(/^\s*<pre[^>]*>(.*)<\/pre>\s*/);
            if (match) {
                try {
                    obj = Ext.decode(match[1]);
                } catch (err) {
                    obj = match[1];
                }
            }
        }
        return obj;
    },
    
    /** private: method[handleUploadSuccess]
     */
    handleUploadSuccess: function(response) {
        Ext.Ajax.request({
            method: "GET",
            url: this._import,
            success: function(response) {
                var details = Ext.decode(response.responseText);
                this.fireEvent("uploadcomplete", this, details);
                delete this._import;
            },
            scope: this
        });
    }

});

/** api: xtype = gxp_layeruploadpanel */
Ext.reg("gxp_layeruploadpanel", gxp.LayerUploadPanel);
