Ext.ns("GeoNode");

/** api: constructor
 *  .. class:: ComposerMixin(config)
 *
 *    A mixin class to add in functions needed by GeoNode.Composer as well as 
 *    an SDK app.
 */
GeoNode.ComposerMixin = {

    /** private: method[checkLayerPermissions]
     *  :arg layerRecord: ``GeoExt.data.LayerRecord`` The currently selected layer.
     *  :arg layerTreeId: ``gxp.LayerTree`` or ``gxp.LayerManager`` The layer tree identifier.
     *
     *  Check the editing permissions on the layer and enable/disable the
     *  editing tools.
     */
    checkLayerPermissions: function (layerRecord, layerTreeId) {
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
        var tree_node =  Ext.getCmp(layerTreeId).getSelectionModel().getSelectedNode();
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
                    url:"/gs/" + layer.params.LAYERS + "/edit-check",
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
        if (this.id) {
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
        }
    },

    /** private: method[getCRSFToken]
     * Read the CSRFToken from the cookie.
     */
    getCRSFToken: function() {
        var csrfToken, csrfMatch = document.cookie.match(/csrftoken=(\w+)/);
        if (csrfMatch && csrfMatch.length > 0) {
            csrfToken = csrfMatch[1];
        }
        return csrfToken;
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
                      OpenLayers.Request.DEFAULT_CONFIG.headers['X-CSRFToken'] = this.getCRSFToken();
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
          var csrfToken = this.getCRSFToken();
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
    }
};
