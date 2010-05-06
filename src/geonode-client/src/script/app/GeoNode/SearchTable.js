/*  A Table for displaying and paging through geonode search results.
TODO 
*Selections*
*/ 

Ext.namespace("GeoNode");

GeoNode.DataCart = Ext.extend(Ext.util.Observable, {
    
    selectedLayersText: 'UT: Selected Layers',
    emptySelectionText: 'UT: No Layers Selected',
    nameText: 'UT: Name',
    
    constructor: function(config) {
        Ext.apply(this, config);
        this.doLayout();
    },
    
    doLayout: function() {
        var listView = new Ext.list.ListView({
            store: this.store,
            multiSelect: true,
            emptyText: this.emptySelectionText,
            reserveScrollOffset: true,
            hideHeaders: true,
            columns: [{
                dataIndex: 'name'
            }]
        });
        listView.render(this.renderTo);
        /*
        var panel = new Ext.Panel({
            title: this.selectedLayersText,
            height: 400,
            layout:'fit',
            items: listView
        });
        panel.render(this.renderTo);
        */
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

    constructor: function(config) {
        Ext.apply(this, config);
        if (!this.searchParams) {
            this.searchParams = {};
        }
        if (!this.searchParams.start) {
            this.searchParams.start = 0;
        }
        if (!this.searchParams.limit) {
            this.searchParams.limit = 10;
        }
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
            ], 
        });
        this.searchStore.on('load', function() {
            this.updateControls();
            if (this.dataCart) {
                this.dataCart.reselect();
            }
        }, this);
    
        this.doLayout();
        this.doSearch();
    },
    
    doSearch: function() {
        this.disableControls();
        this.searchStore.load({params: this.searchParams});
    },

    loadNextBatch: function() {
        this.searchParams.start += this.searchParams.limit;
        this.doSearch();
    },
    
    loadPrevBatch: function() {
        this.searchParams.start -= this.searchParams.limit;
        if (this.searchParams.start < 0) {
            this.searchParams.start = 0;
        }
        this.doSearch();
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

    updateQuery: function() {
        this.searchParams.q = this.queryInput.getValue();
        this.searchParams.start = 0;
        this.doSearch();
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
            sm = new Ext.grid.CheckboxSelectionModel({});
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
          this.disableControls();
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
        
        this.selModel.on('rowselect', function(model, index, record) {
            if (this.indexOfId(record.id) == -1) {
                this.add([record]);
            }
        }, this);
        this.selModel.on('rowdeselect', function(model, index, record) {
            var index = this.indexOfId(record.id)
            if (index != -1) {
                this.removeAt(index);
            }
        }, this);
        
        GeoNode.DataCartStore.superclass.constructor.call(this, config);
    },
    
    reselect: function() {
        var store = this.selModel.grid.store;
        this.each(function(rec) {
            var index = store.indexOfId(rec.id);
            if (index != -1) {
                this.selModel.selectRow(index, true);
            }
            return true;
        }, this);
    }
});

