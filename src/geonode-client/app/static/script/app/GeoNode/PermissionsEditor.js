Ext.namespace("GeoNode");
GeoNode.PermissionsEditor = Ext.extend(Ext.util.Observable, {
    // how do we determine permissions for viewing? one of:
    // ANYONE - all users can view
    // REGISTERED - all logged-in users can view
    // EDITORS - all users in the editor list can view
    viewMode: 'EDITORS', 

    // how do we determine permissions for editing? one of:
    // REGISTERED - all logged-in users can edit
    // EDITORS - all users in the editor list can view
    editMode: 'LIST',

    // a Store with the users that have editor permission
    editors: null,

    // a GeoNode.UserSelector widget for the editor list
    editorChooser: null,

    // a Store with the users that have manager permission
    managers: null,

    // a GeoNode.UserSelector widget for the manager list
    managerChooser: null,

    levels: {
        'admin': 'layer_admin',
        'readwrite': 'layer_readwrite',
        'readonly': 'layer_readonly',
        'none': '_none'
    },

    constructor: function(config) {
        Ext.apply(this, config);
        this.addEvents({ 'updated': true });
        GeoNode.PermissionsEditor.superclass.constructor.call(this, config);
        this.initStores();
        this.readPermissions(config.permissions);
        this.doLayout();
    },

    initStores: function(config) {
        var notifyOfUpdate = (function(t) {
            return function() { return t.fireEvent("updated", t); }
        })(this);
        this.editors = new Ext.data.Store({
            reader: new Ext.data.JsonReader({
                root: 'users',
                totalProperty: 'count',
                fields: [{name: 'username'}]
            }),
            listeners: {
                add: notifyOfUpdate,
                remove: notifyOfUpdate,
                update: notifyOfUpdate
            }
        });
        this.managers = new Ext.data.Store({
            reader: new Ext.data.JsonReader({
                root: 'users',
                totalProperty: 'count',
                fields: [{name: 'username'}]
            }),
            listeners: {
                add: notifyOfUpdate,
                remove: notifyOfUpdate,
                update: notifyOfUpdate
            }
        });
    },

    buildUserChooser: function(cfg) {
        var finalConfig = { owner: this.permissions.owner, userLookup: this.userLookup };
        Ext.apply(finalConfig, cfg);

        return new GeoNode.UserSelector(finalConfig);
    },

    buildViewPermissionChooser: function() {
        return new Ext.Panel({
            border: false,
            items: [
                {html: "<strong>" + gettext("Who can view and download this data?") + "</strong>", flex: 1, border: false},
                { xtype: 'radiogroup', columns: 1, value: this.viewMode, items: [
                    { xtype: 'radio', name: 'viewmode', inputValue: 'ANYONE', boxLabel: gettext( 'Anyone')},
                    { xtype: 'radio', name: 'viewmode', inputValue: 'REGISTERED', boxLabel: gettext('Any registered user')},
                    { xtype: 'radio', name: 'viewmode', inputValue: 'EDITORS', boxLabel: gettext('Only users who can edit')}
                ], listeners: {
                    change: function(grp, checked) {
                        this.viewMode = checked.inputValue;
                        this.fireEvent("updated", this);
                    },
                    scope: this
                }} 
            ]
        }); 
    },

    buildEditPermissionChooser: function() {
        this.editorChooser = this.buildUserChooser({
            store: this.editors,
            availableUserConfig: {
                listeners: {
                    load: function(store, recs, opts) {
                        store.filterBy(function(rec) {
                            return this.editors.findExact("username", rec.get("username")) == -1 
                                && this.managers.findExact("username", rec.get("username")) == -1;
                        }, this);
                    },
                    scope: this
                }
            }
        });

        this.editorChooser.setDisabled(this.editMode !== 'LIST');

        return new Ext.Panel({
            border: false, 
            items: [
                {html: "<strong>" +  gettext('Who can edit this data?') + "</strong>", flex: 1, border: false},
                { xtype: 'radiogroup', columns: 1, value: this.editMode, items: [
                    { xtype: 'radio', name: 'editmode', inputValue: 'REGISTERED', boxLabel: gettext('Any registered user')},
                    { xtype: 'radio', name: 'editmode', inputValue: 'LIST', boxLabel: gettext('Only the following users or groups:')}
                ], listeners: {
                    change: function(grp, checked) {
                        this.editMode = checked.inputValue;
                        this.editorChooser.setDisabled(this.editMode !== 'LIST');
                        this.fireEvent("updated", this);
                    },
                    scope: this
                }},
                this.editorChooser.panel
            ]
        });
    },

    buildManagePermissionChooser: function() {
        this.managerChooser = this.buildUserChooser({
            store: this.managers,
            availableUserConfig: {
                listeners: {
                    load: function(store, recs, opts) {
                        store.filterBy(function(rec) {
                            return this.editors.findExact("username", rec.get("username")) == -1
                                && this.managers.findExact("username", rec.get("username")) == -1;
                        }, this);
                    },
                    scope: this
                }
            }
        });
        return new Ext.Panel({
            border: false, 
            items: [
                {html: "<strong>" +  gettext('Who can manage and edit this data?') + "</strong>", flex: 1, border: false},
                this.managerChooser.panel
            ]
        });
    },

    readPermissions: function(json) {
        this.editors.suspendEvents();
        this.managers.suspendEvents();
        if (json['authenticated'] == this.levels['readwrite']) {
            this.editMode = 'REGISTERED';
        } else if (json['authenticated'] == this.levels['readonly']) {
            this.viewMode = 'REGISTERED';
        }

        if (json['anonymous'] == this.levels['readonly']) {
            this.viewMode = 'ANYONE';
        }

        for (var i = 0; i < json.users.length; i++) {
            if (json.users[i][1] === this.levels['readwrite']) {
                this.editors.add(new this.editors.recordType({username: json.users[i][0]}, i + 500));
            } else if (json.users[i][1] === this.levels['admin']) {
                this.managers.add(new this.managers.recordType({username: json.users[i][0]}, i + 500));
            }
        }

        this.editors.resumeEvents();
        this.managers.resumeEvents();
    },

    // write out permissions to a JSON string, suitable for sending back to the mothership
    writePermissions: function() {
        var anonymousPermissions, authenticatedPermissions, perUserPermissions;
        if (this.viewMode === 'ANYONE') {
            anonymousPermissions = this.levels['readonly'];
        } else {
            anonymousPermissions = this.levels['_none'];
        }

        if (this.editMode === 'REGISTERED') {
            authenticatedPermissions = this.levels['readwrite'];
        } else if (this.viewMode === 'REGISTERED') {
            authenticatedPermissions = this.levels['readonly'];
        } else {
            authenticatedPermissions = this.levels['_none'];
        }

        perUserPermissions = [];
        if (this.editMode === 'LIST') {
            this.editors.each(function(rec) {
                perUserPermissions.push([rec.get("username"), this.levels['readwrite']]);
            }, this);
        }

        this.managers.each(function(rec) {
            perUserPermissions.push([rec.get("username"), this.levels['admin']]);
        }, this);

        return {
            anonymous: anonymousPermissions,
            authenticated: authenticatedPermissions,
            users: perUserPermissions
        };
    },

    doLayout: function() {
        this.container = new Ext.Panel({
            renderTo: this.renderTo,
            border: false,
            items: [
                this.buildViewPermissionChooser(),
                this.buildEditPermissionChooser(),
                this.buildManagePermissionChooser()
            ]
        });
    }
});
