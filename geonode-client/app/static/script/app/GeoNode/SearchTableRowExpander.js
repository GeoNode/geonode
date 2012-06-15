Ext.namespace("GeoNode"); 

GeoNode.SearchTableRowExpander = Ext.extend(Ext.grid.RowExpander, {
    errorText: 'UT: Unable to fetch layer details.',
    loadingText: 'UT: Loading...',
    
    constructor: function(config) {
        this.fetchURL = config.fetchURL; 
        GeoNode.SearchTableRowExpander.superclass.constructor.call(this, config);
    },

    getRowClass : function(record, rowIndex, p, ds){
        p.cols = p.cols-1;
        return this.state[record.id] ? 'x-grid3-row-expanded' : 'x-grid3-row-collapsed';
    },

    fetchBodyContent: function(body, record, index) {
        if(!this.enableCaching){
            this._fetchBodyContent(body, record, index);
        }
        var content = this.bodyContent[record.id];
        if(!content){
            this._fetchBodyContent(body, record, index);
        }
        else {
            body.innerHTML = content;
        }
    },
    
    _fetchBodyContent: function(body, record, index) {
        body.innerHTML = this.loadingText;
        var template_url = this.fetchURL + '?uuid=' + record.get('uuid');
        var this_expander = this;
        Ext.Ajax.request({
            url : template_url,
            method: "GET",
            success: function(result) {
                var content = result.responseText;
                body.innerHTML = content;
                this_expander.bodyContent[record.id] = content;
            },
            failure: function(result) {
                body.innerHTML = this_expander.errorText;
            } 
        });
    },

    beforeExpand : function(record, body, rowIndex){
        if(this.fireEvent('beforeexpand', this, record, body, rowIndex) !== false){
            this.fetchBodyContent(body, record, rowIndex);
            return true;
        }else{
            return false;
        }
    }
});
