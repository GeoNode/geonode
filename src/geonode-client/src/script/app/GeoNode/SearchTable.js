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
            colModel: new Ext.grid.ColumnModel({
                defaults: {sortable: false, menuDisabled: true},
                columns: [
                    sm,
                    {header: this.titleText, dataIndex: 'title'}
                ]
            })
        });
        // data cart items are initially selected
        this.store.on('add', function(store, records, index) {
            sm.selectRow(index, true);
        })


        var clearSelectedButton = new Ext.Button({
            text: this.clearSelectedButtonText,
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
            text: this.clearAllButtonText,
        });
        clearAllButton.on('click', function() {
            this.store.removeAll();
            this.store.reselect();
        }, this);

        var controlsForm = new Ext.Panel({
             frame:false,
             border: false,
             layout: new Ext.layout.HBoxLayout({
                 pack: 'end', 
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
                {name: 'abstract', type: 'string'},
                {name: 'keywords'},
                {name: 'detail', type: 'string'},
                {name: 'attribution'},
                {name: 'download_links'},
                {name: 'metadata_links'},
                {name: 'bbox'}
            ], 
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
            this.searchParams.limit = 10;
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
            var searchButton = new Ext.Button({
                text: this.searchButtonText,
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
        
        var expander = new GeoNode.SearchTableRowExpander({}); 


        tableCfg = {
            store: this.searchStore, 
            plugins: [expander],
            autoExpandColumn: 'title',
            viewConfig: {
                autoFill: true, 
                forceFit: true,
                emptyText: this.noResultsText
            },
            height: 300,
            renderTo: table_el
        };


        var columns = [
            expander,
            {header: this.nameHeaderText,
             dataIndex: 'name',
             id: 'name',
             width: 35,
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
                        allowBlank:true
                     });
        
        this.queryInput.on('specialkey', function(field, e) {
            if (e.getKey() == e.ENTER) {
                this.updateQuery();
            }
        }, this);
        var searchButton = new Ext.Button({
            text: this.searchButtonText,
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
                     searchButton,
                     {'html': '<a href="" class="permalink">' + this.permalinkText + '</a>', border: false}
             ]
         });
         searchForm.render(input_el);

         this.permalink = Ext.get(input_el).query('a.permalink')[0];
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
          this.disableControls();

          if (this.searchParams.q) {
              this.queryInput.setValue(this.searchParams.q);
          }
          this.updatePermalink();
}

});

GeoNode.SearchTableRowExpander = Ext.extend(Ext.grid.RowExpander, {

    abstractText: "UT:Abstract:",
    abstractEmptyText: "UT: No abstract is provided for this layer.",
    attributionEmptyText: "UT: No attribution information is provided for this layer.",
    attributionText: "UT:Provided by:",
    downloadText : "UT:Download:",
    downloadEmptyText: 'UT: No download URLs are defined for this layer.',
    keywordEmptyText: "UT: No keywords are listed for this layer.",
    keywordText: "UT:Keywords:",
    metadataEmptyText: 'UT: No metadata URLs are defined for this layer.',
    metadataText: "UT:Metadata Links:",
    dataDetailText: "UT: Details:",

    constructor: function (config) {
        config.tpl = config.tpl || this.getDefaultTemplate();

        var expander, templateLib;
        expander = this;
        templateLib = this.templateLibrary;
        templateLib.metadataEmptyText = this.metadataEmptyText;
        templateLib.keywordEmptyText = this.keywordEmptyText;
        templateLib.attributionEmptyText = this.attributionEmptyText;
        templateLib.downloadEmptyText = this.downloadEmptyText;
        templateLib.abstractEmptyText = this.abstractEmptyText;
        templateLib.dataDetailText = this.dataDetailText;
        Ext.apply(config.tpl, templateLib);

        GeoNode.SearchTableRowExpander.superclass.constructor.call(this, config);
    },

    getDefaultTemplate: function() {
        return new Ext.Template(
            '<p><b>' + this.abstractText + '</b> {abstract:this.getAbstract}</p>' +
            '<p><b>' + this.attributionText + '</b> {attribution:this.attributionLink}</p>'  +
            '<p><b>' + this.metadataText + '</b> {metadata_links:this.metadataLinks}</p>'  +
            '<p><b>' + this.keywordText + '</b> {keywords:this.keywordList}</p>'  +
            '<p><b>' + this.downloadText + '</b> {download_links:this.downloadLinks}</p>' +
            '<p>{detail:this.detailLink}</p>'
        );
    },

    templateLibrary: {


        getAbstract: function(abstract, values) {
            return abstract || this.abstractEmptyText;
        },

        metadataLinks: function (metadataURLs, values) {
            if (metadataURLs === null  || 
                metadataURLs.length === 0) 
            {
                return "<em>" + this.metadataEmptyText + "</em>"; 
            } else {
                var i, links, len;
                links = [];
                for (i = 0, len = metadataURLs.length; i < len; i++) {
                    links.push("<a href=\"" + metadataURLs[i][2] + "\"> " +
                        metadataURLs[i][1] + "</a>");
                }
                return links.join(", ");
            }
        },
        
        downloadLinks: function(downloadURLs, values) {  
            if (downloadURLs === null  || 
                downloadURLs.length === 0) 
            {
                return "<em>" + this.downloadEmptyText + "</em>"; 
            } else {
                var i, links, len;
                links = [];
                for (i = 0, len = downloadURLs.length; i < len; i++) {
                    links.push("<a class=\"download " + downloadURLs[i][0] + "\" href=\"" + downloadURLs[i][2] + "\"> " +
                        downloadURLs[i][1] + "</a>");
                }
                return links.join(", ");
            }
        },
        
        keywordList: function (keywords, values) {
            if (keywords === null ||
                keywords.length === 0) 
            {
                return "<em>" + this.keywordEmptyText + "</em>"; 
            } else {
                return keywords.join(", ");
            }
        },

        attributionLink: function (attribution, values) {
            if (attribution == null || attribution.href == null || attribution.href == '') {
                return "<em>" + this.attributionEmptyText + "</em>";
            } else {
                return "<a href=\"" + attribution.href + "\"> " + attribution.title + "</a>";
            }
        },
        
        detailLink: function(detail, values) {
            if (detail) {
                return '<a href="' + detail + '">' + this.dataDetailText + '</a>';
            }
            else {
                return '';
            }
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

GeoNode.BBOXConstraintTool = OpenLayers.Class(OpenLayers.Control, {
    
    EVENT_TYPES: ["constraintchanged"],
    
    initialize: function(layer, options) {
        this.EVENT_TYPES = GeoNode.BBOXConstraintTool.prototype.EVENT_TYPES.concat(
            OpenLayers.Control.prototype.EVENT_TYPES);
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        this.layer = layer;
    },

    draw: function() {
        this.box = new OpenLayers.Handler.Box(this,
            {"done": this.boxComplete});
    },
    
    boxComplete: function(bounds) {
        // reject non-boxes (null, Pixel) 
        if (!bounds || bounds.CLASS_NAME != 'OpenLayers.Bounds') {
            return;
        }
    
        var constraint = new OpenLayers.Bounds();
        var scr_verts = bounds.toGeometry().getVertices();
        for (var i = 0; i < scr_verts.length; i++) {
            var pixel = new OpenLayers.Pixel(scr_verts[i].x, scr_verts[i].y);
            var lonlat = this.map.getLonLatFromPixel(pixel);
            constraint.extend(lonlat);
        }
        this.setConstraint(constraint);
    },

    setConstraint: function(bounds) {
        this._clearConstraint();
        this.constraint = bounds;
        this.constraint_ft = new OpenLayers.Feature.Vector(bounds.toGeometry()); 
        this.constraint_ft.state = OpenLayers.State.INSERT;
        this.layer.addFeatures([this.constraint_ft]);
        this.events.triggerEvent("constraintchanged", {'constraint': this.constraint})
    },
    
    clearConstraint: function() {
        this._clearConstraint();
        this.events.triggerEvent("constraintchanged", {'constraint': null}) 
    },
    
    _clearConstraint: function() {
        if (this.constraint_ft) {
            this.layer.removeFeatures([this.constraint_ft]);
            delete this.constraint_ft;            
        }
        if (this.constraint) {
            delete this.constraint;
        }
    },
    
    hasConstraint: function() {
        if (this.constraint) {
            return true;
        }
        else {
            return false;
        }
    },

    activate: function() {
        OpenLayers.Control.prototype.activate.apply(this);
        if (this.box) {
            this.box.activate();
        }
    },
    
    deactivate: function() {
        OpenLayers.Control.prototype.deactivate.apply(this);
        if (this.box) {
            this.box.deactivate();
        }                
    }
});

GeoNode.BoundingBoxWidget = Ext.extend(Ext.util.Observable, {
    drawButtonText: 'UT: Draw',
    clearButtonText: 'UT: Clear',
    zoomSliderTipText: 'UT: Zoom',
    
    constructor: function(config) {
        Ext.apply(this, config);
        this.activated = false;
        this.doLayout();
    },

    doLayout: function() {

        var el = Ext.get(this.renderTo);
        var map_el = el.query('.bbox-map')[0];
        var controls_el = el.query('.bbox-controls')[0];

        this.map = new OpenLayers.Map({
            allOverlays: true,
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            units: "m",
            maxResolution: 156543.0339,
            maxExtent: new OpenLayers.Bounds(
                -20037508.34, -20037508.34,
                 20037508.34,  20037508.34
            ),
            controls: [
                new OpenLayers.Control.Navigation(),
                new OpenLayers.Control.PanPanel(),
                new OpenLayers.Control.ZoomPanel(),            
                new OpenLayers.Control.Attribution()
            ]
        });

        var constraintLayer = new OpenLayers.Layer.Vector("Constraint");
        this.map.addLayers([constraintLayer]);
        
        this.constraintTool = new GeoNode.BBOXConstraintTool(constraintLayer);
        this.map.addControl(this.constraintTool);


        this.mapPanel = new GeoExt.MapPanel({
            layout: "anchor",
            border: true,
            map: this.map,
            renderTo: map_el,
            height: 300,
            zoom: this.map.zoom,
            items: [
                new GeoExt.ZoomSlider({
                    vertical: true,
                    height: 100,
                    plugins: new GeoExt.ZoomSliderTip({
                        template: "<div>"+this.zoomSliderTipText+": {zoom}<div>"
                    })
                })
            ]
        });
        this.map.zoomToMaxExtent();

        
        this.drawButton = new Ext.Button({text: this.drawButtonText, enableToggle: true});
        this.drawButton.on('toggle', function(button, pressed) {
            if (pressed) {
                this.constraintTool.activate();
            }
            else {
                this.constraintTool.deactivate();
            }
        }, this);

        this.clearButton = new Ext.Button({text: this.clearButtonText});
        this.clearButton.on('click', function() {
            this.constraintTool.clearConstraint();
        }, this);
        
        var controlsForm = new Ext.Panel({
             frame:false,
             border: false,
             layout: new Ext.layout.HBoxLayout({
                 //pack: 'end', 
                 defaultMargins: {
                     top: 10,
                     bottom: 10,
                     left: 0,
                     right: 10
                  }
             }),
             items: [this.drawButton, this.clearButton]
         });
         controlsForm.render(controls_el);

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


         this.bgManager = new GeoExplorer.BackgroundLayerManager({
            proxy: this.proxy,
            backgroundLayers: [this.background]
         });
         gxp.util.dispatch(this.bgManager.getBackgroundLoaders(), this.activate, this);
    
    },
    
    isActive: function() {
        return this.enabledCB.checked == true; 
    },
    
    hasConstraint: function() {
        return (this.isActive() &&
                this.constraintTool && 
                this.constraintTool.hasConstraint());
    },
    
    applyConstraint: function(query) {
        if (this.hasConstraint()) {
            var bounds = OpenLayers.Bounds.fromArray(this.constraintTool.constraint.toArray());
            bounds.transform(this.mapPanel.map.projection, new OpenLayers.Projection("EPSG:4326"));
            query.bbox = bounds.toBBOX();
        }
        else {
            // no constraint, don't include.
            delete query.bbox;
        }
    },
    
    initFromQuery: function(grid, query) {  
        this.grid = grid;
        this.grid.on('load', function() {
           // recompute bounds when search results change...
           this.updateBounds();
        }, this);


        if (query.bbox) {
            var bounds = OpenLayers.Bounds.fromString(query.bbox);
            if (bounds) {
                bounds.transform(new OpenLayers.Projection("EPSG:4326"), this.mapPanel.map.projection);
                this.constraintTool.setConstraint(bounds);
                this.enable();
                this.map.zoomToExtent(bounds, true);
                this.map.zoomOut(2);
            }
        }
    },
    
    updateBounds: function() {
        if (!this.activated || this.isActive() || !this.grid) {
            return;
        }
        var newbounds = new OpenLayers.Bounds();
        var hasBounds = false;
        
        this.grid.searchStore.each(function(rec) {
            var bbox = rec.get('bbox');
            var cur_proj = new OpenLayers.Projection("EPSG:4326");
            var map_proj = this.mapPanel.map.projection;
            if (bbox) {
                var lower = new OpenLayers.LonLat(bbox.minx, bbox.miny);
                lower.transform(cur_proj, map_proj);
                newbounds.extend(lower);
                var upper = new OpenLayers.LonLat(bbox.maxx, bbox.maxy);
                upper.transform(cur_proj, map_proj);
                newbounds.extend(upper);
                hasBounds = true;
            }
        }, this);
        
        if (hasBounds) {
            this.map.zoomToExtent(newbounds);
        }
    },
    
    activate: function() {
        this.mapPanel.layers.insert(0, this.bgManager.getBackgroundLayers()); 
        this.map.setBaseLayer(this.mapPanel.layers[0]);
        this.activated = true;
        this.updateBounds();
    },
    
    enable: function() {
        this.enabledCB.checked = true;
        this.drawButton.enable();
        this.clearButton.enable();
    }, 

    disable: function() {
        this.enabledCB.checked = false;
        this.drawButton.toggle(false);
        this.drawButton.disable();
        this.clearButton.disable();
        this.constraintTool.clearConstraint();
    }
});