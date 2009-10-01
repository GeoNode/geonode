Ext.namespace("GeoExplorer");
GeoExplorer.NewSourceWindow = Ext.extend(Ext.Window, {
    
    title: "Add New Server...",
    bodyStyle: "padding: 0px",
    width: 300,
    closeAction: 'hide',
    
    error: null,
    
    initComponent: function() {
        
        this.addEvents("server-added");
        
        this.urlTextField = new Ext.form.TextField({
            fieldLabel: "URL",
            width: 240,
            msgTarget: "under",
            validator: OpenLayers.Function.bind(function() {
                return (this.error == null) ? true : this.error;
            }, this)
        });
        
        this.form = new Ext.form.FormPanel({
            items: [
                this.urlTextField
            ],
            border: false,
            labelWidth: 30,
            bodyStyle: "padding: 5px",
            autoWidth: true,
            autoHeight: true
        });
        
        this.bbar = [
            new Ext.Button({
                text: "Cancel",
                handler: function() {
                    this.hide();
                },
                scope: this
            }),
            new Ext.Toolbar.Fill(),
            new Ext.Button({
                text: "Add Server",
                iconCls: "icon-addlayers",
                handler: function() {
                    // Clear validation before trying again.
                    this.error = null;
                    this.urlTextField.validate();
                    
                    this.fireEvent("server-added", this.urlTextField.getValue());
                }, 
                scope: this
            })
        ];
        
        this.items = this.form;
        
        GeoExplorer.NewSourceWindow.superclass.initComponent.call(this);
        
        this.form.on("render", function() {
            this.loadMask = new Ext.LoadMask(this.form.getEl(), {msg:"Contacting Server..."});
        }, this);
        
        this.on("hide", function() {
            // Reset values so it looks right the next time it pops up.
            this.error = null;
            this.urlTextField.validate(); // Remove error text.
            this.urlTextField.setValue("");
            this.loadMask.hide();
        }, this);
    },
    
    setLoading: function() {
        this.loadMask.show();
    },
    
    setError: function(error) {
        this.loadMask.hide();
        this.error = error;
        this.urlTextField.validate();
    }
});
