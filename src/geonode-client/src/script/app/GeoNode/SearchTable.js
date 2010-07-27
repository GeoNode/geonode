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
           },
           failure: function(result) {
               //console.log(result);
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
                    console.log(result); 
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


GeoNode.DataCart = Ext.extend(Ext.util.Observable, {
    
    selectedLayersText: 'UT: Selected Layers',
    emptySelectionText: 'UT: No Layers Selected',
    titleText: 'UT: Title',
    clearSelectedButtonText: 'UT: Clear Selected',
    clearAllButtonText: 'UT: Clear All',
    
    constructor: function(config) {
        Ext.apply(this, config);
        this.doLayout();
    },

    getSelectedLayerIds: function() {
        var layerIds = [];
        this.grid.selModel.each(function(rec) {
            layerIds.push(rec.get('name'));
        });
        return layerIds;
    },
    
    doLayout: function() {
        var widgetHTML =
        '<div class="selection-table"></div>' +
        '<div class="selection-controls"></div>' +
        '<div class="selection-ops></div>"';
        
        var el = Ext.get(this.renderTo);
        el.update(widgetHTML);
        var controls_el = el.query('.selection-controls')[0];
        var table_el = el.query('.selection-table')[0];
        var ops_el = el.query('.selection-ops')[0];
        
        sm = new Ext.grid.CheckboxSelectionModel({});
        this.grid = new Ext.grid.GridPanel({
            store: this.store,
            viewConfig: {
                autoFill: true,
                forceFit: true,
                emptyText: this.emptySelectionText,
                deferEmptyText: false
            },
            height: 150,
            renderTo: table_el,
            selModel: sm,
            hideHeaders: true,
            colModel: new Ext.grid.ColumnModel({
                defaults: {sortable: false, menuDisabled: true},
                columns: [
                    sm,
                    {dataIndex: 'title'}
                ]
            })
        });
        // data cart items are initially selected
        this.store.on('add', function(store, records, index) {
            sm.selectRow(index, true);
        })


        var clearSelectedButton = new Ext.Button({
            text: this.clearSelectedButtonText
        });
        clearSelectedButton.on('click', function() {
            sm.each(function(rec) {
                var index = this.store.indexOfId(rec.id);
                if (index >= 0) {
                    this.store.removeAt(index);
                }
            }, this);
            this.store.reselect();
        }, this);

        
        var clearAllButton = new Ext.Button({
            text: this.clearAllButtonText
        });
        clearAllButton.on('click', function() {
            this.store.removeAll();
            this.store.reselect();
        }, this);

        var controlsForm = new Ext.Panel({
             frame:false,
             border: false,
             layout: new Ext.layout.HBoxLayout({
                 defaultMargins: {
                     top: 10,
                     bottom: 10,
                     left: 0,
                     right: 0
                  }
             }),
             items: [clearSelectedButton, clearAllButton]
         });
         controlsForm.render(controls_el);
    }
});

GeoNode.SearchTable = Ext.extend(Ext.util.Observable, {
    selectHeaderText: 'UT: Select',
    nameHeaderText: 'UT: Name',
    titleHeaderText: 'UT: Title',
    selectText: 'UT: Select:',
    selectAllText: 'UT: All',
    selectNoneText: 'UT: None',
    previousText: 'UT: Prev',
    nextText: 'UT: Next',
    ofText: 'UT: of',
    noResultsText: 'UT: Your search did not match any items.',
    searchLabelText: 'UT: Search Data',
    searchButtonText: 'UT: Search',
    showingText: 'UT: Showing',
    loadingText: 'UT: Loading',
    permalinkText: 'UT: permalink',

    constructor: function(config) {
        this.addEvents('load'); 
        Ext.apply(this, config);
        this.initFromQuery();
        this.loadData();
    },
    
    loadData: function() {
    
        this.searchStore = new Ext.data.JsonStore({
            url: this.searchURL,
            root: 'rows',
            idProperty: 'name',
            remoteSort: true,
            totalProperty: 'total',
            fields: [
                {name: 'name', type: 'string'},
                {name: 'title', type: 'string'},
                {name: 'uuid', type: 'string'},
                {name: 'abstract', type: 'string'},
                {name: 'keywords'},
                {name: 'detail', type: 'string'},
                {name: 'attribution'},
                {name: 'download_links'},
                {name: 'metadata_links'},
                {name: 'bbox'}
            ]
        });
        this.searchStore.on('load', function() {
            this.updateControls();
            if (this.dataCart) {
                this.dataCart.reselect();
            }
            this.fireEvent('load', this);
        }, this);
        
        this.doLayout();
        this.doSearch();
    },
    
    initFromQuery: function() {
        if (!this.searchParams) {
            this.searchParams = {};
        }
        if (!this.searchParams.start) {
            this.searchParams.start = 0;
        }
        if (!this.searchParams.limit) {
            this.searchParams.limit = 25;
        }
        
        if (this.constraints) {
            for (var i = 0; i < this.constraints.length; i++) {
                this.constraints[i].initFromQuery(this, this.searchParams);
            }
        }
    },
    
    doSearch: function() {
        /* updates parameters from constraints and 
           permforms a new search */
        this.searchParams.start = 0;
        if (this.constraints) {
            for (var i = 0; i < this.constraints.length; i++) {
                this.constraints[i].applyConstraint(this.searchParams);
            }
        }
        this._search(this.searchParams);
    },
    
    
    _search: function(params) {
       /* search with given parameters */  
        this.disableControls();
        this.searchStore.load({params: params});
        this.updatePermalink(params);
    },

    loadNextBatch: function() {
        this.searchParams.start += this.searchParams.limit;
        this._search(this.searchParams);
    },
    
    loadPrevBatch: function() {
        this.searchParams.start -= this.searchParams.limit;
        if (this.searchParams.start < 0) {
            this.searchParams.start = 0;
        }
        this._search(this.searchParams);
    },

    disableControls: function() {
        this.nextButton.setDisabled(true);
        this.prevButton.setDisabled(true);
        this.pagerLabel.setText(this.loadingText);
    },

    updateControls: function() {
        var total = this.searchStore.getTotalCount();

        if (this.searchParams.start > 0) {
            this.prevButton.setDisabled(false);
        }
        else {
            this.prevButton.setDisabled(true);
        }
        
        if (this.searchParams.start + this.searchParams.limit < total) {
            this.nextButton.setDisabled(false);
        }
        else {
            this.nextButton.setDisabled(true);
        }
        
        var minItem = this.searchParams.start + 1;
        var maxItem = minItem + this.searchParams.limit - 1;
        if (maxItem > total) {
            maxItem = total;
        }
        this.pagerLabel.setText(this.showingText + ' ' + minItem  +
                                '-' + maxItem + ' ' + this.ofText + ' ' + 
                                total);
    },

    
    updatePermalink: function() {
        if (this.permalink) {
            this.permalink.href = Ext.urlAppend(this.permalinkURL, Ext.urlEncode(this.searchParams));
        }
    },

    updateQuery: function() {
        /* called when main search query changes */ 
        this.searchParams.q = this.queryInput.getValue();
        this.doSearch();
    },
    
    hookupSearchButtons: function(el) {
        var root = Ext.get(el);
        var buttons = root.query('.search-button');
        for (var i = 0; i < buttons.length; i++) {
            var text = buttons[i].innerHTML || this.searchButtonText;
            Ext.get(buttons[i]).update('');
            var searchButton = new Ext.Button({
                text: text,
                renderTo: buttons[i]
            });
            searchButton.on('click', this.doSearch, this);
        }
    },

    doLayout: function() {
        
        var widgetHTML =
        '<div class="search-results">' +
        '<div class="search-input"></div>' +
        '<div class="search-table"></div>' +
        '<div class="search-controls"></div>' +
        '</div>';
        
        var el = Ext.get(this.renderTo);
        el.update(widgetHTML);
        var input_el = el.query('.search-input')[0];
        var table_el = el.query('.search-table')[0];
        var controls_el = el.query('.search-controls')[0];
        
        var expander = new GeoNode.SearchTableRowExpander({fetchURL: this.layerDetailURL}); 


        tableCfg = {
            store: this.searchStore, 
            plugins: [expander],
            autoExpandColumn: 'title',
            viewConfig: {
                autoFill: true, 
                forceFit: true,
                emptyText: this.noResultsText
            },
            autoHeight: true,
            renderTo: table_el
        };


        var columns = [
            expander,
            {header: this.nameHeaderText,
             dataIndex: 'name',
             hidden: true,
             id: 'name',
             width: 35
            },
            {header: this.titleHeaderText,
             dataIndex: 'title',
             id: 'title',
             renderer: function(value, metaData, record, rowIndex, colIndex, store) {
                 var detail = record.get('detail');
                 if (detail) {
                     return '<a href="' + detail + '">' + value + '</a>';
                 }
                 else {
                     return value;
                 }
             }
             }];
        
        if (this.trackSelection == true) {
            sm = new Ext.grid.CheckboxSelectionModel({checkOnly: true});
            this.dataCart = new GeoNode.DataCartStore({selModel: sm});
            columns.push(sm);
            tableCfg.selModel = sm;
        }
        var colModel = new Ext.grid.ColumnModel({
            defaults: {sortable: false, menuDisabled: true},
            columns: columns
        });
        tableCfg.colModel = colModel;

        this.table = new Ext.grid.GridPanel(tableCfg);
        
        this.queryInput = new Ext.form.TextField({
                        fieldLabel: this.searchLabelText,
                        name: 'search',
                        allowBlank:true,
                        width: 350
                     });
        
        this.queryInput.on('specialkey', function(field, e) {
            if (e.getKey() == e.ENTER) {
                this.updateQuery();
            }
        }, this);
        var searchButton = new Ext.Button({
            text: this.searchButtonText
        });
        searchButton.on('click', this.updateQuery, this)

        var searchForm = new Ext.Panel({
             frame:false,
             border: false,
             layout: new Ext.layout.HBoxLayout({defaultMargins: {
                 top: 10,
                 bottom: 10,
                 left: 0,
                 right: 10
             }}),
             items: [this.queryInput,
                     searchButton
             ]
         });
         searchForm.render(input_el);

         this.prevButton =  new Ext.Button({text: this.previousText});
         this.prevButton.on('click', this.loadPrevBatch, this);
    
         this.nextButton =  new Ext.Button({text: this.nextText});
         this.nextButton.on('click', this.loadNextBatch, this);

         this.pagerLabel = new Ext.form.Label({text: ""});

         var controls = new Ext.Panel({
              frame:false,
              border: false,
              layout: new Ext.layout.HBoxLayout({defaultMargins: {
                  top: 10,
                  bottom: 10,
                  left: 0,
                  right: 10
              }}),
              items: [this.prevButton, this.nextButton, this.pagerLabel]
          });
          controls.render(controls_el);
          this.permalink = Ext.query('a.permalink')[0];
         
          this.disableControls();

          if (this.searchParams.q) {
              this.queryInput.setValue(this.searchParams.q);
          }
          this.updatePermalink();
}

});

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

GeoNode.BoundingBoxWidget = Ext.extend(Ext.util.Observable, {

    /**
     * Property: viewerConfig
     * Options such as background layers configuration to be passed to the
     * gxp.Viewer instance enclosed by this BoundingBoxWidget.
     */
    viewerConfig: null,

    constructor: function(config) {
        Ext.apply(this, config);
        this.activated = false;
        this.doLayout();
    },

    doLayout: function() {

        var el = Ext.get(this.renderTo);

        var viewerConfig = {
            proxy: this.proxy,
            useCapabilities: false,
            useBackgroundCapabilities: false,
            useToolbar: false,
            useMapOverlay: false,
            portalConfig: {
                collapsed: true,
                border: false,
                height: 300,
                renderTo: el.query('.bbox-expand')[0]
            }
        }

        viewerConfig = Ext.apply(viewerConfig, this.viewerConfig)

        this.viewer = new GeoExplorer.Viewer(viewerConfig);

         this.enabledCB = el.query('.bbox-enabled input')[0];        
         this.disable();
         
         Ext.get(this.enabledCB).on('click', function() {
            if (this.enabledCB.checked == true) {
                this.enable();
            }
            else {
                this.disable();
            }
         }, this);

    },
    
    isActive: function() {
        return this.enabledCB.checked == true; 
    },
    
    hasConstraint: function() {
        return this.isActive()
    },
    
    applyConstraint: function(query) {
        /* set parameters in the search query to limit the search to the 
         * displayed bounding box.
         */
        if (this.hasConstraint()) {
            var bounds = this.viewer.mapPanel.map.getExtent();
            bounds.transform(this.viewer.mapPanel.map.getProjectionObject(),
                new OpenLayers.Projection("EPSG:4326"));
            query.bbox = bounds.toBBOX();
        }
        else {
            // no constraint, don't include.
            delete query.bbox;
        }
    },
    
    initFromQuery: function(grid, query) {  
        if (query.bbox) {
            var bounds = OpenLayers.Bounds.fromString(query.bbox);
            if (bounds) {
                bounds.transform(new OpenLayers.Projection("EPSG:4326"),
                    this.viewer.mapPanel.map.getProjectionObject());
                this.enable();
                this.viewer.mapPanel.map.zoomToExtent(bounds, true);
            }
        }
    },
    
    activate: function() {
        this.activated = true;
    },
    
    enable: function() {
        this.enabledCB.checked = true;
        this.viewer.portal.expand();
    }, 

    disable: function() {
        this.enabledCB.checked = false;
        this.viewer.portal && this.viewer.portal.collapse();
    }
});
