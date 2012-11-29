Ext.namespace("GeoNode"); 

GeoNode.DataCartStore = Ext.extend(Ext.data.Store, {

    constructor : function(config) {
        this.selModel = config.selModel;
        this.reselecting = false;
        
        this.selModel.on('rowselect', function(model, index, record) {
            if (this.reselecting == true) {
                return;
            }
    
            if (this.indexOfId(record.id) == -1) {
                this.add([record]);
            }
        }, this);
        this.selModel.on('rowdeselect', function(model, index, record) {
            if (this.reselecting == true) {
                return;
            }

            var index = this.indexOfId(record.id)
            if (index != -1) {
                this.removeAt(index);
            }
        }, this);
        
        GeoNode.DataCartStore.superclass.constructor.call(this, config);
    },
    
    reselect: function() {
        this.reselecting = true;
        this.selModel.clearSelections();
        var store = this.selModel.grid.store;
        this.each(function(rec) {
            var index = store.indexOfId(rec.id);
            if (index != -1) {
                this.selModel.selectRow(index, true);
            }
            return true;
        }, this);
        this.reselecting = false;
    }
});

