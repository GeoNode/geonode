Ext.namespace("GeoNode");

GeoNode.BatchDownloadWidget = Ext.extend(Ext.util.Observable, {

    downloadingText: 'UT: Downloading...',
    cancelText: 'UT: Cancel',
    windowMessageText: 'UT: Please wait',
    
    constructor: function(config) {
        Ext.apply(this, config);
        this.beginDownload();
    },
    
    beginDownload: function() {
        // XXX could confirm download here. 
        var this_widget = this;
        Ext.Ajax.request({
           url: this.begin_download_url,
           method: 'POST',
           params: {layer: this.layers, format: this.format},
           success: function(result) {
               var result = Ext.util.JSON.decode(result.responseText);
               this_widget.monitorDownload(result.id);
           }
        });
    },
    
    monitorDownload: function(download_id) {
        var checkStatus; 
        var this_widget = this;
                
        var pb = new Ext.ProgressBar({
            text: this.downloadingText
        });

        var cancel_download = function() { 
            Ext.Ajax.request({
                url : this_widget.stop_download_url + download_id,
                method: "GET",
                success: function(result) {
                    clearInterval(checkStatus);
                },
                failure: function(result) { 
                    clearInterval(checkStatus); // break if something fails
                } 
        })};
        
        var win = new Ext.Window({
            width: 250,
            height: 100,
            plain: true,
            modal: true,
            closable: false,
            hideBorders: true,
            items: [pb],
            buttons: [
                {text: this.cancelText,
                handler: function() {
                    cancel_download();
                    win.hide();
                }}
            ]
        });


        var update_progress = function() { 
            Ext.Ajax.request({ 
                url : this_widget.begin_download_url + '?id='+ download_id,
                method: "GET",
                success: function(result) {
                    var process = Ext.util.JSON.decode(result.responseText);
                    if (process["process"]["status"] === "FINISHED"){ 
                        clearInterval(checkStatus); 
                        pb.updateProgress(1,"Done....",true);
                        win.close();
                        location.href = this_widget.download_url + download_id;
                    }
                    else {
                        pb.updateProgress(process["process"]["progress"]/100, this_widget.downloadingText,true); 
                    }
                },
                failure: function(result) { 
                    //console.log(result); 
                    clearInterval(checkStatus);
                    win.close();
                }});
        };
        checkStatus = setInterval(update_progress, 1000);
        win.show();
    }
     
});

