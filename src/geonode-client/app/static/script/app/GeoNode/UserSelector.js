Ext.namespace("GeoNode");
GeoNode.UserSelector = Ext.extend(Ext.util.Observable, {
    constructor: function(config) {
        Ext.apply(this, config);
        this.initUserStore();
        this.panel = this.doLayout();
    },

    initUserStore: function() {
        if (!this.userstore) {
            var cfg = {
                proxy: new Ext.data.HttpProxy({ url: this.userLookup, method: 'POST' }),
                reader: new Ext.data.JsonReader({
                    root: 'users',
                    totalProperty: 'count',
                    fields: [{name: 'username'}]
                })
            };
            Ext.apply(cfg, this.availableUserConfig || {});
            this.userstore = new Ext.data.Store(cfg);
            this.userstore.load({params: {query: ''}});
        }

        if (!this.store) {
            this.store = new Ext.data.ArrayStore({
                idIndex: 0,
                fields: ['username'],
                data: []
            });
        }
    },

    doLayout: function() {
        var owner = this.owner;
        var plugin = (function() {
            var view;
            function init(v) {
                view = v;
                view.on('render', addHooks);
            }

            function addHooks() {
                view.getEl().on('mousedown', removeItem, this, { delegate: 'button' });
            }

            function removeItem(e, target) {
                var item = view.findItemFromChild(target);
                var idx = view.indexOf(item);
                var rec = view.store.getAt(idx);
                if (rec.get("username") !== owner) {
                    view.store.removeAt(view.indexOf(item));
                }
            }

            return { init: init };
        })();

        this.selectedUsers = new Ext.DataView({
            store: this.store,
            itemSelector: 'div.user_item',
            tpl: new Ext.XTemplate('<div><tpl for="."> <div class="x-btn user_item"><button class="icon-removeuser remove-button">&nbsp;</button>{username}</div></tpl></div>'),
            plugins: [plugin],
            autoHeight: true,
            multiSelect: true
        });

        function addSelectedUser() {
            var value = this.availableUsers.getValue();
            var index = this.availableUsers.store.findExact('username', value);
            if (index != -1 &&
                this.selectedUsers.store.findExact('username', value) == -1
            ) {
                this.selectedUsers.store.add([this.availableUsers.store.getAt(index)]);
                this.availableUsers.reset();
            }
        }

        this.addButton = new Ext.Button({ 
            iconCls: 'icon-adduser',
            handler: addSelectedUser,
            scope: this
        });

        this.availableUsers = new Ext.form.ComboBox({
            width: 180,
            store: this.userstore,
            typeAhead: true,
            minChars: 0,
            align: 'right',
            border: 'false',
            displayField: 'username',
            emptyText: gettext("Add user..."),
            listeners: {
                scope: this,
                select: addSelectedUser
            }
        });

        return new Ext.Panel({
            border: false,
            renderTo: this.renderTo,
            items: [
                this.selectedUsers,
                { layout: 'hbox', border: false, items: [ this.addButton, this.availableUsers ]}
            ]
        });
    },

    setDisabled: function(disabled) {
        this.selectedUsers.setDisabled(disabled);
        this.availableUsers.setDisabled(disabled);
        this.addButton.setDisabled(disabled);
    }
});
