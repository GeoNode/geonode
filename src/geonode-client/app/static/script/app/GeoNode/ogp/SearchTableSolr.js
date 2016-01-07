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

    searchOnLoad: false,
    linkableTitle: true,

    constructor: function(config) {
        this.addEvents('load'); 
        Ext.apply(this, config);
        this.initFromQuery();
        this.loadData();
    },
    
    loadData: function() {
    
        this.searchStore = new Ext.data.JsonStore({
            url: this.searchURL,
            root: 'response.docs',
            idProperty: 'LayerId',
            remoteSort: true,
            totalProperty: 'response.numFound',
            baseParams: {
                wt: 'json',
                defType: 'edismax',
                qf: 'LayerDisplayNameSynonyms^0.2 ThemeKeywordsSynonymsIso^0.1 ThemeKeywordsSynonymsLcsh^0.1 PlaceKeywordsSynonyms^0.1 Publisher^0.1 Originator^0.1'
            },
            fields: [
                {name: 'Name', type: 'string'},
                {name: 'LayerDisplayName', type: 'string'},
                {name: 'LayerId', type: 'string'}
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

        if (this.searchOnLoad)
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
        
        if (this.queryInput.getValue() === ''){
            this.searchParams.q = '*';
        }

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
        this.pagerLabel.setText(this.loadingText);
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
            this.permalink.href = Ext.urlAppend(this.permalinkURL, Ext.urlEncode(this.searchParams));
        }
    },

    updateQuery: function() {
        /* called when main search query changes */ 
        this.searchParams.fq = []; 
        this.searchParams.q = this.queryInput.getValue();
        if (this.originatorInput.getValue() !== ''){
            this.searchParams.fq.push('Originator:' + this.originatorInput.getValue());
        }
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

        var unviewableTooltip = this.unviewableTooltip;
        var remoteTooltip = this.remoteTooltip;
        
        var columns = [
            expander,
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
                sortable: true,
                renderer: function(value, metaData, record, rowIndex, colIndex, store) {
                    
                    var detail = value;
                    
                    return detail;
                }
            },
            
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

        this.originatorInput = new Ext.form.TextField({
                        emptyText: this.originatorSearchLabelText,
                        name: 'search_originator',
                        allowBlank: true,
                        width: 100
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
                     this.originatorInput,
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
