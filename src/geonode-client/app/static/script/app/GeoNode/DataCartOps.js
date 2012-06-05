Ext.namespace("GeoNode");

GeoNode.DataCartOps = Ext.extend(Ext.util.Observable, {

    failureText: 'UT: Operation Failed',
    noLayersText: 'UT: No layers are currently selected.',

    constructor: function(config) {
        Ext.apply(this, config);
        this.doLayout();
    },
   
    doLayout: function() {
        var el = Ext.get(this.renderTo);
        var createMapLink = Ext.get(el.query('a.create-map')[0]);
        this.createMapForm = Ext.get(el.query('#create_map_form')[0]);
        
        createMapLink.on('click', function(evt) {
            evt.preventDefault();
            var layers = this.cart.getSelectedLayerIds();
            if (layers && layers.length) {
                this.createNewMap(layers);
            }
            else {
                Ext.MessageBox.alert(this.failureText, this.noLayersText);
            }
        }, this);
        
        batch_links = el.query('a.batch-download');
        for (var i = 0; i < batch_links.length; i++) {
           var bel = Ext.get(batch_links[i]);
           bel.on('click', function(e, t, o) {
               e.preventDefault();
               var layers = this.cart.getSelectedLayerIds();
               if (layers && layers.length) {
                   var format = Ext.get(t).getAttribute('href').substr(1);
                   this.batchDownload(layers, format);
               }
               else {
                   Ext.MessageBox.alert(this.failureText, this.noLayersText);
               }
           }, this);
        }
    },
    
    createNewMap: function(layerIds) {
        var inputs = [];
        for (var i = 0; i < layerIds.length; i++) {
            inputs.push({
                tag: 'input',
                type: 'hidden',
                name: 'layer',
                value: layerIds[i]
            });
        }
        inputs.push({
            tag: 'input',
            type: 'hidden',
            name: 'csrfmiddlewaretoken',
            value: Ext.util.Cookies.get("csrftoken")
        });
        Ext.DomHelper.overwrite(this.createMapForm, {'tag': 'div', cn: inputs});
        this.createMapForm.dom.submit();
    },
    
    batchDownload: function(layerIds, format) {
        // alert('Batch Download');
        new GeoNode.BatchDownloadWidget({
            layers: layerIds,
            format: format,
            begin_download_url: this.begin_download_url,
            stop_download_url: this.stop_download_url,
            download_url: this.download_url
        });
    }
    
});
