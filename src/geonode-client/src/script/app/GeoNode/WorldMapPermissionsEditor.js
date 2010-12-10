Ext.namespace("GeoNode");
GeoNode.WorldMapPermissionsEditor = Ext.extend(Ext.util.Observable, {
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
        this.userset = {};
    },

    buildUserChooser: function() {


        var chooser = new Ext.form.TextField({ 
            width: 150,
            vtype: 'email',
            emptyText: gettext("Type an email")
        });

        return new Ext.Panel({
            border: false,
            layout: 'hbox',
            items: [
                new Ext.Button({
                    iconCls: 'icon-add',
                    handler: function() {
                        if (chooser.getValue() != this.permissions.email && chooser.isValid() && chooser.getValue() != ''
                            && !this.userset[chooser.getValue()]
                        ) {
                            this.addUser({
                                email: chooser.getValue(),
                                role: this.permissions.authenticated
                            });
                        }
                        chooser.setValue(null);
                    },
                    scope: this
                }),
                { html: gettext("Add user"), flex: 1, border: false },
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
                    width: 100,
                    align: 'right',
                    border: false,
                    cls: 'x-span-font-eight',
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
        this.userset[user] = true;
        var up = this.userPanel;

        var userEditor = new Ext.Panel({
            border: false,
            layout: 'hbox',
            items: [
                new Ext.Button({
                    iconCls: 'icon-removelayers',
                    handler: function() {
                        var params = {};
                        params['user.' + user.email] = "";
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
                { flex: 1, html: '<span class="x-span-font-eight">' + user.email + '</span>', border: false },
                new Ext.form.ComboBox({ 
                    width: 100,
                    align: 'right',
                    border: false,
                    cls: 'x-span-font-eight',
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
                            params["user." + user.email] = rec.get("identifier");
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
            if (this.permissions.users[i][0] != this.permissions.owner) {
                this.addUser({
                    email: this.permissions.users[i][0],
                    role: this.permissions.users[i][1]
                });
            }
        }

        var addUserPanel = this.buildUserChooser();

        this.container = new Ext.Panel({
            renderTo: this.renderTo,
            border: false,
            items: [
                this.buildGroupPermissionCombo(
                    {displayname: gettext('Anyone'), identifier: 'anonymous'},
                    this.permissions.anonymous
                ),
                this.buildGroupPermissionCombo(
                    {displayname: gettext('Authenticated Users'), identifier: 'authenticated'},
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
