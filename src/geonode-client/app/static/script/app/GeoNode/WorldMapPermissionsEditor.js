Ext.namespace("GeoNode");
GeoNode.WorldMapPermissionsEditor = Ext.extend(Ext.util.Observable, {
    // how do we determine permissions for viewing? one of:
    // ANYONE - all users can view
    // REGISTERED - all logged-in users can view
    // EDITORS - all users in the editor list can view
    // CUSTOMGROUP - all uses in the custom group can view
    viewMode: 'EDITORS',

    customGroup: '',

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
        GeoNode.WorldMapPermissionsEditor.superclass.constructor.call(this, config);
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
                fields: [{name: 'email'},{name: 'user'}]
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
                fields: [{name: 'email'},{name: 'user'}]
            }),
            listeners: {
                add: notifyOfUpdate,
                remove: notifyOfUpdate,
                update: notifyOfUpdate
            }
        });
    },

    buildUserChooser: function(cfg) {
        var finalConfig = { owner: this.permissions.owner_email, userLookup: this.userLookup };
        Ext.apply(finalConfig, cfg);
        return new GeoNode.UserEmailSelector(finalConfig);
    },

    buildViewPermissionChooser: function() {

        var radioItems = [
                    { xtype: 'radio', name: 'viewmode', inputValue: 'ANYONE', boxLabel: gettext( 'Anyone')},
                    { xtype: 'radio', name: 'viewmode', inputValue: 'REGISTERED', boxLabel: gettext('Any registered user')}
        ];

        if (this.customGroup)
        {
            radioItems.push({ xtype: 'radio', name: 'viewmode', inputValue: 'CUSTOM', boxLabel: this.customGroup});
        }

        radioItems.push({ xtype: 'radio', name: 'viewmode', inputValue: 'EDITORS', boxLabel: gettext('Only users who can edit')});


        return new Ext.Panel({
            border: false,
            items: [
                {html: "<strong>" + gettext("Who can view or download this?") + "</strong>", flex: 1, border: false},
                { xtype: 'radiogroup', columns: 1, value: this.viewMode, items: radioItems, listeners: {
                    change: function(grp, checked) {
                        if (checked != null)
                        {
                            this.viewMode = checked.inputValue;
                            this.fireEvent("updated", this);
                        }
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
                            return this.editors.findExact("email", rec.get("email")) == -1
                                && this.managers.findExact("email", rec.get("email")) == -1;
                        }, this);
                    },
                    scope: this
                }
            }
        });

        this.editorChooser.setDisabled(this.editMode !== 'LIST');

        var radioItems = [
                    { xtype: 'radio', name: 'editmode', inputValue: 'ANYONE', boxLabel: gettext( 'Anyone')},
                    { xtype: 'radio', name: 'editmode', inputValue: 'REGISTERED', boxLabel: gettext('Any registered user')}
        ];

        if (this.customGroup)
        {
            radioItems.push({ xtype: 'radio', name: 'editmode', inputValue: 'CUSTOM', boxLabel: this.customGroup});
        }

        radioItems.push({ xtype: 'radio', name: 'editmode', inputValue: 'LIST', boxLabel: gettext('Only users who can edit')});


        return new Ext.Panel({
            border: false,
            items: [
                {html: "<strong>" +  gettext('Who can edit this?') + "</strong>", flex: 1, border: false},
                { xtype: 'radiogroup', columns: 1, value: this.editMode, items: radioItems,
                  listeners: {
                    change: function(grp, checked) {
                        if (checked != null) {
                            this.editMode = checked.inputValue;
                            this.editorChooser.setDisabled(this.editMode !== 'LIST');
                            this.fireEvent("updated", this);
                        }
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
                            return this.editors.findExact("email", rec.get("email")) == -1
                                && this.managers.findExact("email", rec.get("email")) == -1;
                        }, this);
                    },
                    scope: this
                }
            }
        });
        return new Ext.Panel({
            border: false,
            items: [
                {html: "<strong>" +  gettext('Who can manage and edit this?') + "</strong>", flex: 1, border: false},
                this.managerChooser.panel
            ]
        });
    },

    readPermissions: function(json) {
        this.editors.suspendEvents();
        this.managers.suspendEvents();

        if (json['authenticated'] == this.levels['readwrite']) {
            this.editMode = 'REGISTERED';
        } else if (json['customgroup'] == this.levels['readwrite']) {
            this.editMode = 'CUSTOM';
        } else
            this.editMode = 'LIST'

        if (json['anonymous'] == this.levels['readonly']) {
            this.viewMode = 'ANYONE';
        }
        else if (json['authenticated'] == this.levels['readonly']) {
            this.viewMode = 'REGISTERED';
        }
        else if (json['customgroup'] == this.levels['readonly']) {
            this.viewMode = 'CUSTOM';
        }



        for (var i = 0; i < json.users.length; i++) {
            if (json.users[i][1] === this.levels['readwrite']) {
                this.editors.add(new this.editors.recordType({email: json.users[i][0], user: json.names[i][1]}, i + 500));
            } else if (json.users[i][1] === this.levels['admin']) {
                this.managers.add(new this.managers.recordType({email: json.users[i][0], user: json.names[i][1]}, i + 500));
            }
        }

        this.editors.resumeEvents();
        this.managers.resumeEvents();
    },

    // write out permissions to a JSON string, suitable for sending back to the mothership
    writePermissions: function() {
        var anonymousPermissions, authenticatedPermissions, customPermissions, perUserPermissions;

        if (this.viewMode === 'ANYONE') {
            anonymousPermissions = this.levels['readonly'];
        } else {
            anonymousPermissions = this.levels['none'];
        }



        if (this.editMode === 'CUSTOM') {
            customPermissions = this.levels['readwrite'];
            if (this.viewMode === 'CUSTOM') {
                authenticatedPermissions = this.levels['none'];
            } else if (this.viewMode === 'REGISTERED') {
                authenticatedPermissions = this.levels['readonly'];
            } else {
                authenticatedPermissions = this.levels['none'];
            }
        }
        else if (this.viewMode === 'CUSTOM') {
            customPermissions = this.levels['readonly'];
            authenticatedPermissions = this.levels['none'];
        }
        else if (this.editMode === 'REGISTERED') {
            authenticatedPermissions = this.levels['readwrite'];
            customPermissions = this.levels['readwrite'];
        }
        else if (this.viewMode === 'REGISTERED') {
            authenticatedPermissions = this.levels['readonly'];
            customPermissions = this.levels['readonly'];
        }
        else {
            authenticatedPermissions = this.levels['none'];
            customPermissions = this.levels['none'];
        }


        perUserPermissions = [];
        if (this.editMode === 'LIST') {
            this.editors.each(function(rec) {
                perUserPermissions.push([rec.get("email"), this.levels['readwrite']]);
            }, this);
        }



        this.managers.each(function(rec) {
            perUserPermissions.push([rec.get("email"), this.levels['admin']]);
        }, this);


        return {
            anonymous: anonymousPermissions,
            authenticated: authenticatedPermissions,
            customgroup: customPermissions,
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
