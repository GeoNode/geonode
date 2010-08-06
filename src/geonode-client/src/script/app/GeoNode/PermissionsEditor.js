Ext.namespace("GeoNode");
GeoNode.PermissionsEditor = Ext.extend(Ext.util.Observable, {
    constructor: function(config) {
        Ext.apply(this, config);
        this.initPermissionStore();
        this.doLayout();
    },

    initPermissionStore: function() {
        this.permissionStore = new Ext.data.ArrayStore({
            data: this.permissions.levels,
            idIndex: 0,
            fields: [
                {name: "identifier"},
                {name: "displayname"}
            ]
        });
    },

    buildUserChooser: function() {
        var userStore = new Ext.data.Store({
            proxy: new Ext.data.HttpProxy({ url: '/accounts/ajax_lookup' }),
            reader: new Ext.data.JsonReader({
                root: 'users',
                totalProperty: 'count',
                fields: [{name: 'username'}]
            })
        });

        var chooser = new Ext.form.ComboBox({ 
            width: 120,
            typeAhead: true,
            minChars: 2,
            align: 'right',
            border: false,
            store: userStore,
            displayField: 'username'
        });

        return new Ext.Panel({
            border: false,
            layout: 'hbox',
            items: [
                new Ext.Button({
                    iconCls: 'icon-addlayers',
                    handler: function() {
                        var idx = chooser.getStore().findExact(
                            "username",
                            chooser.getValue()
                        );
                        if (idx >= 0) {
                            this.addUser({
                                username: chooser.getValue(),
                                role: this.permissions.authenticated
                            });
                        }
                        chooser.setValue(null);
                    },
                    scope: this
                }),
                { html: "Add user", flex: 1, border: false },
                chooser
            ]
        }); 
    },

    buildGroupPermissionCombo: function(group, permission) {
        return new Ext.Panel({
            border: false,
            layout: 'hbox',
            items: [
                {html: group.displayname, flex: 1, border: false},
                new Ext.form.ComboBox({ 
                    width: 120,
                    align: 'right',
                    border: false,
                    store: this.permissionStore,
                    value: permission,
                    displayField: "displayname",
                    valueField: "identifier",
                    mode: 'local',
                    editable: false,
                    triggerAction: 'all',
                    listeners: {
                        select: function(cb, rec, idx) {
                            var params = {};
                            params[group.identifier] = rec.get('identifier');
                            Ext.Ajax.request({
                                params: params,
                                url: this.submitTo
                            });
                        },
                        scope: this
                    }
                })
            ]
        }); 
    },

    addUser: function(user) {
        var up = this.userPanel;

        var userEditor = new Ext.Panel({
            border: false,
            layout: 'hbox',
            items: [
                new Ext.Button({
                    iconCls: 'icon-removelayers',
                    handler: function() {
                        var params = {};
                        params['user.' + user.username] = "";
                        Ext.Ajax.request({
                            params: params,
                            url: this.submitTo,
                            success: function() {
                                up.remove(userEditor);
                            }
                        });
                    },
                    scope: this
                }),
                { flex: 1, html: user.username, border: false },
                new Ext.form.ComboBox({ 
                    width: 120,
                    align: 'right',
                    border: false,
                    store: this.permissionStore,
                    displayField: "displayname",
                    valueField: "identifier",
                    value: user.role,
                    mode: 'local',
                    editable: false,
                    triggerAction: 'all',
                    listeners: {
                        select: function(cb, rec, index) {
                            var params = {};
                            params["user." + user.username] = rec.get("identifier");
                            Ext.Ajax.request({
                                params: params,
                                url: this.submitTo
                            });
                        },
                        scope: this
                    }
                })
            ]
        });

        this.userPanel.add(userEditor);
        this.userPanel.doLayout();
    },

    doLayout: function() {
        this.userPanel = new Ext.Panel({
            border: false
        });

        for (var i = 0; i < this.permissions.users.length; i++) {
            this.addUser({
                username: this.permissions.users[i][0],
                role: this.permissions.users[i][1]
            });
        }

        var addUserPanel = this.buildUserChooser();

        this.container = new Ext.Panel({
            renderTo: this.renderTo,
            border: false,
            items: [
                this.buildGroupPermissionCombo(
                    {displayname: 'Anyone', identifier: 'anonymous'},
                    this.permissions.anonymous
                ),
                this.buildGroupPermissionCombo(
                    {displayname: 'Authenticated Users', identifier: 'authenticated'},
                    this.permissions.authenticated
                ),
                {html: '<hr/>', border: false},
                this.userPanel,
                {html: '<hr/>', border: false},
                addUserPanel
            ]
        });
    }
});
