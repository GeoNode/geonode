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
    searchLabelText: 'Keyword',
    searchButtonText: 'UT: Search',
    showingText: 'UT: Showing',
    loadingText: 'UT: Loading',
    permalinkText: 'UT: permalink',
    unviewableTooltip: 'UT: Unviewable Data',
    remoteTooltip: 'UT: Remote Data',
    invalidQueryText: 'Invalid Query',
    searchTermRequired: 'You need to specify a search term',
    originatorSearchLabelText: 'Source',
    dataTypeSearchLableText: 'UT: Data Type',
    originatorText: 'Source',

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
            idProperty: 'id',
            remoteSort: true,
            totalProperty: 'response.numFound',
            fields: [
                {name: 'id', type: 'string'},
                {name: 'name', type: 'string'},
                {name: 'title', type: 'string'},
                {name: 'abstract', type: 'string'},
                {name: 'min_x', type: 'string'},
                {name: 'min_y', type: 'string'},
                {name: 'max_x', type: 'string'},
                {name: 'max_y', type: 'string'},
                {name: 'layer_originator', type: 'string'},
                {name: 'is_public', type: 'string'},
                {name: 'url', type: 'string'},
                {name: 'service_type', type: 'string'},
                {name: 'bbox', type: 'string'},
                {name: 'location', type: 'string'},
                {name: 'layer_date', type: 'string'},
                {name: 'layer_datetype', type: 'string'},
                // not used?
                {name: 'Availability', type: 'string'},
                {name: 'LayerUsername', type: 'string'}

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
                var timeout = null;
                $(row).on('mouseover', function(){
                    // set a small timeout so to not add new layers while the mouse is
                    // just passing on the list
                    timeout = setTimeout(function(){self.doMouseoverOn(index)}, 20);
                });

                $(row).on('mouseout', function(){
                    if(timeout |= null){
                        self.doMouseoverOff(index);
                    };
                    clearTimeout(timeout);
                });
            });

            // use jquery to remove tooltip on mouseleave
            $('.x-grid3-row').mouseleave(function(){
                $('.x-tip').hide();
                $('.x-shadow').hide();
            });
        }, this);

        // hack to fix the sort term as solr is expecting it
        this.searchStore.on('beforeload', function(scope, options){
            if(scope.sortInfo){
                options.params.sort = options.params.sort + ' ' + scope.sortInfo.direction;
            }
        });

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
        if (!GeoNode.queryTerms.rows) {
            GeoNode.queryTerms.rows = 200;
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
        GeoNode.queryTerms.start += GeoNode.queryTerms.rows;
        this._search(GeoNode.queryTerms);
    },

    loadPrevBatch: function() {
        GeoNode.queryTerms.start -= GeoNode.queryTerms.rows;
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

        if (GeoNode.queryTerms.start + GeoNode.queryTerms.rows < total) {
            this.nextButton.setDisabled(false);
        }
        else {
            this.nextButton.setDisabled(true);
        }

        var minItem = GeoNode.queryTerms.start + 1;
        var maxItem = minItem + GeoNode.queryTerms.rows - 1;
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

        // Remove any layer_originator filter if there
        for(var i=0;i<GeoNode.queryTerms.fq.length;i++){
            if(GeoNode.queryTerms.fq[i].indexOf('layer_originator') > -1){
                GeoNode.queryTerms.fq.splice(i, 1);
            }
        };
        if (this.originatorInput.getValue() !== ''){
            GeoNode.queryTerms.fq.push('layer_originator:*' + this.originatorInput.getValue() + '*');
        }

        // Remove any DataType filter if there
        for(var i=0;i<GeoNode.queryTerms.fq.length;i++){
            if(GeoNode.queryTerms.fq[i].indexOf('service_type') > -1){
                GeoNode.queryTerms.fq.splice(i, 1);
            }
        };
        var datatypes = this.dataTypeInput.getValue();
        if(datatypes !== ''){
            GeoNode.queryTerms.fq.push(datatypes);
        };

        // Remove any date filter if there
        for(var i=0;i<GeoNode.queryTerms.fq.length;i++){
            if(GeoNode.queryTerms.fq[i].indexOf('layer_date') > -1){
                GeoNode.queryTerms.fq.splice(i, 1);
            }
        };
        var dates = this.dateInput.getDateValues();
        if(dates != '[* TO *]'){
            GeoNode.queryTerms.fq.push("layer_date:" + this.dateInput.getDateValues());
        };

        if (this.queryInput.getValue() === ''){
            GeoNode.queryTerms.q = '*';
        }

        GeoNode.queryTerms.start = 0;

        // now trigger the heatmap update
        this.heatmap.fireEvent('fireSearch', false);


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
        var self = this;

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
        var controls_el = Ext.get('search_controls');


        var sm = new Ext.grid.RowSelectionModel({
            listeners:{
                rowselect: function(sm, rowIndex, record){
                    if(record.get('is_public')){
                        self.heatmap.bbox_widget.viewer.fireEvent('showLayer',
                        self.getlayerTypename(record), self.getLayerID(record));
                    }
                },
                rowdeselect: function(sm, rowIndex, record){
                    self.heatmap.bbox_widget.viewer.fireEvent('hideLayer',
                        self.getlayerTypename(record));
                }
            }
        });
        sm.handleMouseDown = function(g, rowIndex, e){
            var view = this.grid.getView();
            var isSelected = this.isSelected(rowIndex);
            if(isSelected){
                this.deselectRow(rowIndex);
            }else{
                this.selectRow(rowIndex, true);
                view.focusRow(rowIndex);
            }
        };

        this.dataCart = new GeoNode.DataCartStore({selModel: sm});

        tableCfg = {
            store: this.searchStore,
            viewConfig: {
                autoFill: true,
                forceFit: true,
                emptyText: this.noResultsText
            },
            renderTo: 'search_results',
            height: 310,
            sm: sm
        };

        var unviewableTooltip = this.unviewableTooltip;
        var remoteTooltip = this.remoteTooltip;

        var columns = [
            {
                header: this.titleHeaderText,
                dataIndex: 'title',
                id: 'title',
                sortable: true,
                width: 200,
                sortBy: 'LayerTitle',
                renderer: function(value, metadata, record, rowIndex, colIndex, store){

                    var the_abstract = app.layerTree.replaceURLWithHTMLLinks(record.get('abstract'));
                    metadata.attr =
                        'ext:qtip="<strong>Title: ' + record.get('title') +
                        '</strong><br/><strong>Source: ' + record.get('layer_originator') +
                        '</strong><br/><strong>Abstract</strong>: ' +
                        the_abstract.substring(0, 250) +
                        '<br/><strong>Date</strong>: ' + record.get('layer_datetype') + '"';
                    return $.parseJSON(record.get('is_public')) ?  value : '<span class="unviewable-layer"></span>' + '  ' + value;

                }
            },
            {
                header: this.originatorText,
                dataIndex: 'layer_originator',
                id: 'layer_originator',
                width: 100,
                sortable: true
            },
            {
                header: 'Date',
                id: 'date',
                width: 50,
                sortable: true,
                dataIndex: 'layer_date',
                sortBy: 'layer_date',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var solr_date_array = record.get('layer_date').split('-');
                    if(solr_date_array.length == 1){
                      return 'None';
                    }
                    if (solr_date_array[0] == ''){
                      return '-' + parseInt(solr_date_array[1], 10);
                    } else {
                      return parseInt(solr_date_array[0], 10);
                    };
                }
            }
        ];

        var colModel = new Ext.grid.ColumnModel({
            defaults: {sortable: true, menuDisabled: true},
            columns: columns
        });
        tableCfg.colModel = colModel;

        this.table = new Ext.grid.GridPanel(tableCfg);

        this.queryInput = new Ext.form.TextField({
                        emptyText: this.searchLabelText,
                        name: 'search',
                        allowBlank: true,
                        width: 90,
                        height: 25,
                        cls: 'search-bar'
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
                        width: 90,
                        height: 25,
                        cls: 'search-bar'
        });
        this.originatorInput.on('specialkey', function(field, e) {
            if (e.getKey() == e.ENTER) {
                this.updateQuery();
            }
        }, this);

        this.dataTypeInput = new Ext.form.ComboBox({
            id: 'dataTypes',
            mode: 'local',
            width: 110,
            height: 25,
            cls: 'data-type layer-selection',
            store: new Ext.data.ArrayStore({
                id: 0,
                fields: [
                    'value',
                    'Label'
                ],
                data: [['', 'All Layers'],
                    ['service_type:"Hypermap:WorldMap"', 'WorldMap Layers'],
                    ['service_type:"OGC:WMTS"', 'WMTS'],
                    ['service_type:"OGC:WMS"', 'WMS'],
                    ['service_type:"ESRI:ArcGIS:ImageServer"', 'ESRI Image'],
                    ['service_type:"ESRI:ArcGIS:MapServer"', 'ESRI Map']
                ]
            }),
            valueField: 'value',
            displayField: 'Label',
            triggerAction: 'all',
            editable: false,
            forceSelection: true,
            value: ''
        });
        this.dataTypeInput.on('specialkey', function(field, e) {
            if (e.getKey() == e.ENTER) {
                this.updateQuery();
            }
        }, this);

        var dateStartTextField = new Ext.form.TextField({
            name: 'startDate',
            width: 160,
            height: 25,
            listeners: {
                change: function(scope, newValue, oldValue){
                    self.dateInput.valuesFromInput(0, newValue);
                    self.updateQuery();
                },
                keypress: function(scope, e){
                    if (e.getKey() == e.ENTER) {
                        e.stopPropagation();
                        scope.fireEvent('change', scope, scope.getValue());
                    }
                }
            },
            enableKeyEvents: true
        });

        var dateEndTextField = new Ext.form.TextField({
            name: 'endDate',
            width: 160,
            height: 25,
            listeners: {
                change: function(scope, newValue, oldValue){
                    self.dateInput.valuesFromInput(1, newValue);
                    self.updateQuery();
                },
                keypress: function(scope, e){
                    if (e.getKey() == e.ENTER) {
                        e.stopPropagation();
                        scope.fireEvent('change', scope, scope.getValue());
                    }
                }
            },
            enableKeyEvents: true
        });

        this.dateLabelPanel = new Ext.Panel({
            items: [new Ext.form.Label({text: 'from year'}), dateStartTextField, new Ext.form.Label({text: 'to year'}), dateEndTextField],
            cls: 'search-bar date-form'
        });

        this.dateInput = new GeoNode.TimeSlider();

        // updates the dates in the dates text fields
        function updateTextDates(){
            var values = self.dateInput.valuesToTime();
            dateStartTextField.setValue(values[0]);
            dateEndTextField.setValue(values[1]);
        }
        updateTextDates();
        this.dateInput.addListener('change', function(){
            updateTextDates();
        });
        this.dateInput.addListener('changecomplete', function(){
            self.updateQuery();
        });

        var searchButton = new Ext.Button({
            text: this.searchButtonText,
            iconCls: 'prominent-btn',
            cls: 'search-bar search-button'
        });
        searchButton.on('click', this.updateQuery, this);

        var clearSearchLink = new Ext.Button({
            text: "Reset",
            iconCls: 'not-prominent-btn',
            cls: 'search-bar clear-search-button',
            listeners: {
                click: function(){self.clearSearch()}
            }
        });

        var searchForm = new Ext.Panel({
             frame: false,
             border: false,
             layout: 'table',
             layoutConfig: {
                columns: 4,
                tableAttrs: {
                    style: {
                        width: '100%'
                    }
                }
            },
            defaults: {
                bodyStyle:'border: 0px; padding: 0 10px 10px 10px;'
            },
            items: [{
                items: [
                    this.queryInput,
                    this.originatorInput,
                    this.dataTypeInput, //dropdown
                    searchButton,
                    clearSearchLink
                ],
                colspan: 4
            },{
                items: [
                  this.dateLabelPanel
                ],
                colspan: 4
            },{
                items: [this.dateInput],
                colspan: 4
            }]
         });
         searchForm.render(input_el);

         this.prevButton =  new Ext.Button({text: this.previousText, iconCls:"prominent-btn small-btn"});
         this.prevButton.on('click', this.loadPrevBatch, this);

         this.nextButton =  new Ext.Button({text: this.nextText, iconCls:"prominent-btn small-btn"});
         this.nextButton.on('click', this.loadNextBatch, this);

         this.pagerLabel = new Ext.form.Label({text: "", cls: "pager-label"});

         var controls = new Ext.Panel({
              frame:false,
              border: false,
              layout: new Ext.layout.HBoxLayout({defaultMargins: {
                  top: 10,
                  bottom: 10,
                  left: 0,
                  right: 5
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
        this.showPreviewLayer(element);

    },

    doMouseoverOff: function(){
        this.hideBounds();
        this.hidePreviewLayer();
    },

    showBounds : function(element) {
        var bbox = this.getLayerBounds(element);
        this.heatmap.bbox_widget.viewer.fireEvent("showBBox", bbox);
    },

    getLayerBounds: function(element){
        var bbox = {};
        bbox.south = element.data.min_y
        bbox.north = element.data.max_y
        bbox.west = element.data.min_x
        bbox.east = element.data.max_x
        return bbox
    },

    hideBounds : function() {
        this.heatmap.bbox_widget.viewer.fireEvent("hideBBox");
    },

    showPreviewLayer: function(record){

        if($.parseJSON(record.get('is_public'))){
            var typename = this.getlayerTypename(record);
            this.heatmap.bbox_widget.viewer.fireEvent("showPreviewLayer", typename, this.getLayerID(record));
        }
    },

    hidePreviewLayer: function(){
        this.heatmap.bbox_widget.viewer.fireEvent("hidePreviewLayer");
    },

    getlayerTypename: function(record){
        return record.get('name');
    },

    getLayerID: function(record){
        return record.get('id');
    },

    clearSearch: function(){
        this.originatorInput.setValue('');
        this.dataTypeInput.setValue('');
        this.dateInput.setValue(0, this.dateInput.values[0]);
        this.dateInput.setValue(1, this.dateInput.values[1]);
        this.queryInput.setValue('');
        delete this.table.store.sortInfo;
        this.updateQuery();
    }
});
