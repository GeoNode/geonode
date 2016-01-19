Ext.namespace("GeoNode"); 

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
    searchLabelText: 'UT: Keyword',
    searchButtonText: 'UT: Search',
    showingText: 'UT: Showing',
    loadingText: 'UT: Loading',
    permalinkText: 'UT: permalink',
    unviewableTooltip: 'UT: Unviewable Data',
    remoteTooltip: 'UT: Remote Data',
    invalidQueryText: 'Invalid Query', 
    searchTermRequired: 'You need to specify a search term',
    originatorSearchLabelText: 'UT: Originator',
    dataTypeSearchLableText: 'UT: Data Type',
    originatorText: 'UT: Originator',

    searchOnLoad: false,
    linkableTitle: true,

    constructor: function(config) {
        this.addEvents('load'); 
        Ext.apply(this, config);
        this.initFromQuery();
        this.loadData();

        // give a reference of this to heatmap to enable cross search
        this.heatmap.searchTable = this;
    },
    
    loadData: function() {
        var self = this;
    
        this.searchStore = new Ext.data.JsonStore({
            url: this.searchURL,
            root: 'response.docs',
            idProperty: 'LayerId',
            remoteSort: true,
            totalProperty: 'response.numFound',
            fields: [
                {name: 'Name', type: 'string'},
                {name: 'LayerDisplayName', type: 'string'},
                {name: 'LayerId', type: 'string'},
                {name: 'MinX', type: 'string'},
                {name: 'MinY', type: 'string'},
                {name: 'MaxX', type: 'string'},
                {name: 'MaxY', type: 'string'},
                {name: 'Originator', type: 'string'}
            ]
        });
        this.searchStore.on('load', function() {
            this.updateControls();
            if (this.dataCart) {
                this.dataCart.reselect();
            }
            this.fireEvent('load', this);
            var rows = this.table.getView().getRows();
            $.each(rows, function(index, row){
                $(row).on('mouseover', function(){
                    self.doMouseoverOn(index);
                });

                $(row).on('mouseout', function(){
                    self.doMouseoverOff(index);
                });
            });
        }, this);
        
        this.doLayout();

        if (this.searchOnLoad)
            this.doSearch();
    },

    initFromQuery: function() {
        if (!GeoNode.queryTerms) {
            GeoNode.queryTerms = {};
        }
        if (!GeoNode.queryTerms.start) {
            GeoNode.queryTerms.start = 0;
        }
        if (!GeoNode.queryTerms.limit) {
            GeoNode.queryTerms.limit = 100;
        }
        
        if (this.constraints) {
            for (var i = 0; i < this.constraints.length; i++) {
                this.constraints[i].initFromQuery(this, GeoNode.queryTerms);
            }
        }
    },
    
    doSearch: function() {
        /* updates parameters from constraints and 
           permforms a new search */
        
        if (this.queryInput.getValue() === ''){
            GeoNode.queryTerms.q = '*';
        }

        GeoNode.queryTerms.start = 0;
        
        this._search(GeoNode.queryTerms);
    },
    
    
    _search: function(params) {
       /* search with given parameters */  
        this.disableControls();
        this.pagerLabel.setText(this.loadingText);
        this.searchStore.load({params: params});
        this.updatePermalink(params);
    },

    loadNextBatch: function() {
        GeoNode.queryTerms.start += GeoNode.queryTerms.limit;
        this._search(GeoNode.queryTerms);
    },
    
    loadPrevBatch: function() {
        GeoNode.queryTerms.start -= GeoNode.queryTerms.limit;
        if (GeoNode.queryTerms.start < 0) {
            GeoNode.queryTerms.start = 0;
        }
        this._search(GeoNode.queryTerms);
    },

    disableControls: function() {
        this.nextButton.setDisabled(true);
        this.prevButton.setDisabled(true);
    },

    updateControls: function() {
        var total = this.searchStore.getTotalCount();

        if (GeoNode.queryTerms.start > 0) {
            this.prevButton.setDisabled(false);
        }
        else {
            this.prevButton.setDisabled(true);
        }
        
        if (GeoNode.queryTerms.start + GeoNode.queryTerms.limit < total) {
            this.nextButton.setDisabled(false);
        }
        else {
            this.nextButton.setDisabled(true);
        }
        
        var minItem = GeoNode.queryTerms.start + 1;
        var maxItem = minItem + GeoNode.queryTerms.limit - 1;
        if (minItem > total) {
            minItem = total;
        }
        if (maxItem > total) {
            maxItem = total;
        }
        this.pagerLabel.setText(this.showingText + ' ' + minItem  +
                                '-' + maxItem + ' ' + this.ofText + ' ' + 
                                total);
    },

    updatePermalink: function() {
        if (this.permalink) {
            this.permalink.href = Ext.urlAppend(this.permalinkURL, Ext.urlEncode(GeoNode.queryTerms));
        }
    },

    updateQuery: function() {
        /* called when main search query changes */
        GeoNode.queryTerms.q = this.queryInput.getValue();
        if (this.originatorInput.getValue() !== ''){
            GeoNode.queryTerms.fq.push('Originator:' + this.originatorInput.getValue());
        }

        // Remove any DataType filter if there
        for(var i=0;i<GeoNode.queryTerms.fq.length;i++){
            if(GeoNode.queryTerms.fq[i].indexOf('DataType') > -1){
                GeoNode.queryTerms.fq.splice(i, 1);
            }
        };
        var datetypes = this.dataTypeInput.getValue();
        if (datetypes.length > 0 && datetypes < 4){
            var values = datetypes;
            var string = '';
            for(var i=0;i<values.length;i++){
                string += 'DataType:' + values[i].name + ' OR ';
            }
            string = string.slice(0, -4);
            GeoNode.queryTerms.fq.push(string);
        }
        this.doSearch();

        // now trigger the heatmap update
        this.heatmap.fireEvent('fireSearch', false);
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
        
        //var expander = new GeoNode.SearchTableRowExpander({fetchURL: this.layerDetailURL});


        tableCfg = {
            store: this.searchStore, 
            viewConfig: {
                autoFill: true,
                forceFit: true,
                emptyText: this.noResultsText
            },
            autoHeight: true,
            renderTo: table_el
        };

        var unviewableTooltip = this.unviewableTooltip;
        var remoteTooltip = this.remoteTooltip;
        
        var columns = [
            //expander,
            /*
            {header: this.nameHeaderText,
             dataIndex: 'name',
             hidden: true,
             id: 'name',
             width: 35
            },*/
            {
                header: this.titleHeaderText,
                dataIndex: 'LayerDisplayName',
                id: 'title',
                sortable: true
            },
            {
                header: this.originatorText,
                dataIndex: 'Originator',
                id: 'originator',
                sortable: true
            }
            
        ];
        
        if (this.trackSelection == true) {
            sm = new Ext.grid.CheckboxSelectionModel({
                checkOnly: true,
                renderer: function(v, p, record){
                    /*
                     *  A bit of a hack. CheckboxSelectionModel's
                     *  mousedown selection behavior
                     *  is tied to rendered div's class.
                     */
                    
                     return '<div class="x-grid3-row-checker">&#160;</div>';
                    
                }
            });

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
                        emptyText: this.searchLabelText,
                        name: 'search',
                        allowBlank: true,
                        width: 350
                     });
        this.queryInput.on('specialkey', function(field, e) {
            if (e.getKey() == e.ENTER) {
                this.updateQuery();
            }
        }, this);

        this.originatorInput = new Ext.form.TextField({
                        emptyText: this.originatorSearchLabelText,
                        name: 'search_originator',
                        allowBlank: true,
                        width: 100
        });
        
        this.dataTypeInput = new Ext.form.CheckboxGroup({
            id: 'dataTypes',
            fieldLabel: 'Data Type',
            items: [
                {boxLabel: 'Worldmap Vector', name: 'Vector', checked: true},
                {boxLabel: 'Worldmap', name: 'Raster', checked: true},
                {boxLabel: 'ESRI Services', name: 'RESTServices', checked: true},
                {boxLabel: 'WMS Services', name: 'WMSServices', checked: true}
            ]
        });

        
        var searchButton = new Ext.Button({
            text: this.searchButtonText
        });
        searchButton.on('click', this.updateQuery, this)

        var searchForm = new Ext.Panel({
             frame: false,
             border: false,
             layout: 'table',
             layoutConfig: {
                columns: 3
            },
            defaults: {
                bodyStyle:'border: 0px; padding: 10px;'
            },
            items: [{
                items: [
                    this.queryInput,
                    this.originatorInput
                ],
                colspan: 3
            },{
                items: [this.dataTypeInput],
                colspan: 3
            },{
                items: [searchButton],
                colspan: 1
            }]

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

          this.updatePermalink();
    },

    doMouseoverOn : function(index){
        var element = this.table.getStore().getAt(index);
        this.showBounds(element);
    },
    
    doMouseoverOff: function(){
        this.hideBounds();
    },
    
    showBounds : function(element) {
        var bbox = {};
        bbox.south = element.data.MinY
        bbox.north = element.data.MaxY
        bbox.west = element.data.MinX
        bbox.east = element.data.MaxX
        this.heatmap.bbox_widget.viewer.fireEvent("showBBox", bbox);
    },
    
    hideBounds : function() {
        this.heatmap.bbox_widget.viewer.fireEvent("hideBBox");
    }

});
