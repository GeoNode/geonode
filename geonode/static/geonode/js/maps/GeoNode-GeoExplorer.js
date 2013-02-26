Ext.ns("GeoNode.plugins");
/** api: constructor
 *  .. class:: LayerInfo(config)
 *
 *    Plugin for navigating to the GeoNode layer info page.
 *    Will only be enabled for local layers.
 */
GeoNode.plugins.LayerInfo = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_removelayer */
    ptype: "gn_layerinfo",

    /** api: config[menuText]
     *  ``String``
     *  i18n text to use on the menu item.
     */
    menuText: "Layer Info",

    /** api: config[iconCls]
     *  ``String``
     *  iconCls to use on the menu item.
     */
    iconCls: "gxp-icon-layerproperties",

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = GeoNode.plugins.LayerInfo.superclass.addActions.apply(this, [{
            menuText: this.menuText,
            iconCls: this.iconCls,
            disabled: true,
            handler: function() {
                // TODO is there a way to get this from a template variable?
                var url = "/layers/" + this.target.selectedLayer.get("name");
                window.open(url);
            },
            scope: this
        }]);
        var layerInfoAction = actions[0];

        this.target.on("layerselectionchange", function(record) {
            layerInfoAction.setDisabled(!record || !record.get('restUrl'));
        }, this);
        return actions;
    }
});

Ext.preg(GeoNode.plugins.LayerInfo.prototype.ptype, GeoNode.plugins.LayerInfo);

/** api: constructor
 *  .. class:: Composer(config)
 *   
 *    The GeoNode Composer application class.
 *    Changes compared to out-of-the-box GeoExplorer:
 *    - before saving a map, show a metadata form
 *    - add a tool that will show the map title and that will have a clickable
 *      link.
 *    - a generic XHRTrouble dialog that gives easier access to underlying
 *      Django errors.
 *    - adds catalogue search through the GeoNode search api
 *    - only enable editing if user has the right permissions
 *    - integrate with GeoNode AJAX login
 *    - publish map will show the iframe text directly, and not a wizard
 *      like interface that GeoExplorer has
 *    - when saving a map, do not set window.location.hash
 *    - use different urls for saving a new map and updating an existing map
 *      than GeoExplorer does.
 */
GeoNode.Composer = Ext.extend(GeoExplorer.Composer, {

    /** begin i18n */
    metadataFormCancelText : "UT:Cancel",
    metadataFormSaveAsCopyText : "UT:Save as Copy",
    metadataFormSaveText : "UT:Save",
    metaDataHeader: 'UT:About this Map',
    metaDataMapAbstract: 'UT:Abstract',
    metaDataMapTitle: 'UT:Title',
    connErrorTitleText: "UT:Connection Error",
    connErrorText: "UT:The server returned an error",
    connErrorDetailsText: "UT:Details...",
    /** end i18n */

    ajaxLoginUrl: null,

    /** private: method[constructor]
     *  Construct the composer.
     */
    constructor: function(config) {
        this.titleTemplate = new Ext.Template("<a class='maplist' href='" + this.rest + "'>Maps</a> / <strong>{title}");
        // global request proxy and error handling
        OpenLayers.Request.events.on({
            "failure": function(evt) {
                this.displayXHRTrouble(evt.request);
            },
            scope: this
        });
        Ext.util.Observable.observeClass(Ext.data.Connection);
        Ext.data.Connection.on({
            "requestexception": function(conn, response, options) {
                if(!options.failure) {
                    var url = options.url;
                    if (response.status === 401 && url.indexOf("http" !== 0) &&
                                            url.indexOf(this.proxy) === -1) {
                        this.authenticate(options);
                    } else if (response.status != 405 && url != "/geoserver/rest/styles") {
                        // 405 from /rest/styles is ok because we use it to
                        // test whether we're authenticated or not
                        this.displayXHRTrouble(response);
                    }
                }
            },
            scope: this
        });
        GeoNode.Composer.superclass.constructor.apply(this, [config]);
    },
    /** private: method[showUrl]
     *  Do not show the url after map save.
     */
    showUrl: Ext.emptyFn,
    /** private: method[getPermalink]
     *  :return: ``String``
     *
     *  Get the permalink for the current map.
     */
    getPermalink: function() {
        permalinkTemplate = new Ext.Template("{protocol}//{host}/maps/{id}");
        return permalinkTemplate.apply({
            protocol: window.location.protocol,
            host: window.location.host,
            id: this.id
        });
    },
    /** private: getMapTitle
     *  :return: ``String``
     *
     *  Get the HTML to use in the map title container which is shown in the
     *  top right of the panel top toolbar.
     */
    getMapTitle: function() {
        var title;
        if (this.id) {
            title = '<a class="link" href="' + this.getPermalink(this.id) + '">' + this.about.title + '</a>';
        } else {
            title = "This map is currently unsaved";
        }
        return this.titleTemplate.apply({title: title});
    },
    /** private: method[createTools]
     * Create the toolbar configuration for the main panel.  This method can be 
     * extended by derived explorer classes such as :class:`GeoExplorer.Composer`
     * or :class:`GeoExplorer.Viewer` to provide specialized controls.
     */
    createTools: function() {
        GeoNode.Composer.superclass.createTools.apply(this, arguments);
        new Ext.Container({style: "margin-right: 10px", id: "map-title-header", html: this.getMapTitle()});
    },
    /** api: method[loadConfig]
     *  :arg config: ``Object`` The config object passed to the constructor.
     *
     *  Subclasses that load config asynchronously can override this to load
     *  any configuration before applyConfig is called.
     */
    loadConfig: function(config) {
        // find out what the key of the local source is
        var catalogSourceKey, key;
        for (key in config.sources) {
            var source = config.sources[key];
            if (source.ptype === "gxp_wmscsource" && source.restUrl) {
                catalogSourceKey = key;
                break;
            }
        }
        for (var i=0, ii=config.tools.length; i<ii; i++) {
            if (config.tools[i].ptype === "gxp_addlayers") {
                config.tools[i].search = true;
                config.tools[i].catalogSourceKey = catalogSourceKey;
                config.tools[i].feeds = true;
                break;
            }
        }
        // add catalog source
        config.sources['search'] = {
            ptype: "gxp_geonodecataloguesource",
            restUrl: "/gs/rest",
            url: "/search/api"
        };
        config.tools.push({
            actions: ["map-title-header"],
            actionTarget: "paneltbar"
        }, {
            ptype: "gn_layerinfo",
            actionTarget: ["layers.contextMenu"]
        }, {
            ptype: "gxp_getfeedfeatureinfo"
        });
        GeoNode.Composer.superclass.loadConfig.apply(this, arguments);
        for (key in this.tools) {
            var tool = this.tools[key];
            if (tool.id === "featuremanager") {
                tool.on("layerchange", function(mgr, layer, schema) {
                    this.checkLayerPermissions(layer);
                }, this);
                break;
            }
        }
    },
    /** private: method[checkLayerPermissions]
     *  :arg layerRecord: ``GeoExt.data.LayerRecord`` The currently selected layer.
     *
     *  Check the editing permissions on the layer and enable/disable the
     *  editing tools.
     */
    checkLayerPermissions: function (layerRecord) {
        var buttons;
        for (var key in this.tools) {
            var tool = this.tools[key];
            if (tool instanceof gxp.plugins.FeatureEditor) {
                buttons = tool.actions;
                break;
            }
        }
        var toggleButtons = function(enabled) {
            for (var i = 0; i < buttons.length; i++) {
                enabled ? buttons[i].enable() : buttons[i].disable();
            }
        };
        //Disable if layer is null or selected layer in tree doesn't match input layer
        var tree_node =  Ext.getCmp("layers").getSelectionModel().getSelectedNode();
        if (layerRecord === null) {
            toggleButtons(false);
        }
        else {
            //Proceed if this is a local queryable WMS layer
            var layer = layerRecord.getLayer();
            if (layer instanceof OpenLayers.Layer.WMS && (layer.url == "/geoserver/wms" ||
                    layer.url.indexOf(app.localGeoServerBaseUrl.replace(app.urlPortRegEx, "$1/")) === 0)) {
                Ext.Ajax.request({
                    /* TODO: use a template variable here if possible */
                    url:"/layers/" + layer.params.LAYERS + "/edit-check",
                    method:"POST",
                    success:function (response) {
                        var result = Ext.decode(response.responseText);
                        if (result.authorized === false) {
                            toggleButtons(false);
                        } else {
                            layer.displayOutsideMaxExtent = true;
                            toggleButtons(true);
                        }
                    },
                    failure:function () {
                        toggleButtons(false);
                    }
                });
            } else {
                toggleButtons(false);
            }
        }
    },
    /* TODO: we are overriding a private method here for now
     * The true solution would involve fixing: 
     * https://github.com/opengeo/gxp/issues/163
     */
    showEmbedWindow: function() {
        new Ext.Window({
            title: this.publishActionText,
            layout: "fit",
            width: 380,
            autoHeight: true,
            items: [{
                xtype: "gxp_embedmapdialog",
                url: this.rest + this.id + "/embed"
            }]
        }).show();
    },
    /** private method[displayXHRTrouble]
     *  :arg respoonse: ``Object`` The XHR response object.
     *
     *  If something goes wrong with an AJAX request, show an error dialog
     *  with a button to view the details (Django error).
     */
    displayXHRTrouble: function(response) {
        response.status && Ext.Msg.show({
            title: this.connErrorTitleText,
            msg: this.connErrorText +
                ": " + response.status + " " + response.statusText,
            icon: Ext.MessageBox.ERROR,
            buttons: {ok: this.connErrorDetailsText, cancel: true},
            fn: function(result) {
                if(result == "ok") {
                    var details = new Ext.Window({
                        title: response.status + " " + response.statusText,
                        width: 400,
                        height: 300,
                        items: {
                            xtype: "container",
                            cls: "error-details",
                            html: response.responseText
                        },
                        autoScroll: true,
                        buttons: [{
                            text: "OK",
                            handler: function() { details.close(); }
                        }]
                    });
                    details.show();
                }
            }
        });
    },
    /** private: method[authenticate]
     * Show the login dialog for the user to login.
     */
    authenticate: function(options) {
        var submit = function() {
            form.getForm().submit({
                  waitMsg: "Logging in...",
                  success: function(form, action) {
                      this.setAuthorizedRoles(["ROLE_ADMINISTRATOR"]);
                      win.close();
                      document.cookie = action.response.getResponseHeader("Set-Cookie");
                      // resend the original request
                      if (options) {
                          Ext.Ajax.request(options);
                      }
                  },
                  failure: function(form, action) {
                      var username = form.items.get(0);
                      var password = form.items.get(1);
                      username.markInvalid();
                      password.markInvalid();
                      username.focus(true);
                  },
                  scope: this
              });
          }.createDelegate(this);
          var csrfToken, csrfMatch = document.cookie.match(/csrftoken=(\w+);/);
          if (csrfMatch && csrfMatch.length > 0) {
              csrfToken = csrfMatch[1];
          }
          var win = new Ext.Window({
              title: "GeoNode Login",
              modal: true,
              width: 230,
              autoHeight: true,
              layout: "fit",
              items: [{
                  xtype: "form",
                  autoHeight: true,
                  labelWidth: 55,
                  border: false,
                  bodyStyle: "padding: 10px;",
                  url: this.ajaxLoginUrl,
                  waitMsgTarget: true,
                  errorReader: {
                      // teach ExtJS a bit of RESTfulness
                      read: function(response) {
                          return {
                              success: response.status == 200,
                              records: []
                          };
                      }
                  },
                  defaults: {
                      anchor: "100%"
                  },
                  items: [{
                      xtype: "textfield",
                      name: "username",
                      fieldLabel: "Username"
                  }, {
                      xtype: "textfield",
                      name: "password",
                      fieldLabel: "Password",
                      inputType: "password"
                  }, {
                      xtype: "hidden",
                      name: "csrfmiddlewaretoken",
                      value: csrfToken
                  }, {
                      xtype: "button",
                      text: "Login",
                      inputType: "submit",
                      handler: submit
                  }]
              }],
              keys: {
                  "key": Ext.EventObject.ENTER,
                  "fn": submit
              }
          });
          win.show();
          var form = win.items.get(0);
          form.items.get(0).focus(false, 100);
    },
    initPortal: function() {
        this.on("save", function(id) {
            Ext.getCmp("map-title-header").update(this.getMapTitle());
        }, this);
        this.on("beforesave", function(requestConfig, callback) {
            if (this._doSave === true) {
                delete this._doSave;
                if (this.id) {
                    requestConfig.url = this.rest + this.id + "/data";
                } else {
                    requestConfig.url = this.rest + "new/data";
                }
                return true;
            } else {
                this.showMetadataForm(callback);
                return false;
            }
        }, this);
        this.on("beforehashchange", function(hash) {
            return false;
        });
        GeoNode.Composer.superclass.initPortal.apply(this, arguments);
    },
    /** private: method[initMetadataForm]
     *
     * Initialize metadata entry form.
     */
    initMetadataForm: function(callback){

        var titleField = new Ext.form.TextField({
            width: '95%',
            fieldLabel: this.metaDataMapTitle,
            value: this.about.title,
            allowBlank: false,
            enableKeyEvents: true,
            listeners: {
                "valid": function() {
                    saveAsButton.enable();
                    saveButton.enable();
                },
                "invalid": function() {
                    saveAsButton.disable();
                    saveButton.disable();
                }
            }
        });

        var abstractField = new Ext.form.TextArea({
            width: '95%',
            height: 200,
            fieldLabel: this.metaDataMapAbstract,
            value: this.about["abstract"]
        });

        var metaDataPanel = new Ext.FormPanel({
            bodyStyle: {padding: "5px"},
            labelAlign: "top",
            items: [
                titleField,
                abstractField
            ]
        });
        metaDataPanel.enable();

        var saveAsButton = new Ext.Button({
            text: this.metadataFormSaveAsCopyText,
            disabled: !this.about.title,
            handler: function(e){
                delete this.id;
                this.about.title = titleField.getValue();
                this.about["abstract"] = abstractField.getValue();
                this.metadataForm.hide();
                this._doSave = true;
                this.save(this.metadataForm.saveCallback);
            },
            scope: this
        });
        var saveButton = new Ext.Button({
            text: this.metadataFormSaveText,
            disabled: !this.about.title,
            handler: function(e){
                this.about.title = titleField.getValue();
                this.about["abstract"] = abstractField.getValue();
                this.metadataForm.hide();
                this._doSave = true;
                this.save(this.metadataForm.saveCallback);
            },
            scope: this
        });

        this.metadataForm = new Ext.Window({
            title: this.metaDataHeader,
            closeAction: 'hide',
            saveCallback: callback,
            items: metaDataPanel,
            modal: true,
            width: 400,
            autoHeight: true,
            bbar: [
                "->",
                saveAsButton,
                saveButton,
                new Ext.Button({
                    text: this.metadataFormCancelText,
                    handler: function() {
                        titleField.setValue(this.about.title);
                        abstractField.setValue(this.about["abstract"]);
                        this.metadataForm.hide();
                    },
                    scope: this
                })
            ]
        });
    },

    /** private: method[showMetadataForm]
     *  Shows the window with a metadata form
     */
    showMetadataForm: function(callback) {
        if(!this.metadataForm) {
            this.initMetadataForm(callback);
        } else {
            this.metadataForm.saveCallback = callback;
        }
        this.metadataForm.show();
    }

});
