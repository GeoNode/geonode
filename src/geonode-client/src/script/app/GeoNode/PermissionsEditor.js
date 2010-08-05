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
                        this.addUser({
                            username: chooser.getValue(),
                            role: this.permissions.authenticated
                        });
                    },
                    scope: this
                }),
                {html: "Add user or group", flex: 1, border: false},
                chooser
            ]
        }); 
    },

    buildGroupPermissionCombo: function(group, permission) {
        return new Ext.Panel({
            border: false,
            layout: 'hbox',
            items: [
                {html: group, flex: 1, border: false},
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
                            alert(rec.get("displayname"));
                        }
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
                        // TODO: Remove user from ACL
                        up.remove(userEditor);
                    }
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
                            // user.username, rec.get("displayname")
                            // TODO: Update role for user
                        }
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

        this.addUser({
            username: "dwins",
            role: "map_readwrite"
        });

        var addUserPanel = this.buildUserChooser();

        this.container = new Ext.Panel({
            renderTo: this.renderTo,
            border: false,
            items: [
                this.buildGroupPermissionCombo('Anyone', this.permissions.anonymous),
                this.buildGroupPermissionCombo(
                    'Authenticated Users', this.permissions.authenticated
                ),
                {html: '<hr/>', border: false},
                this.userPanel,
                {html: '<hr/>', border: false},
                addUserPanel
            ]
        });
    }
});
