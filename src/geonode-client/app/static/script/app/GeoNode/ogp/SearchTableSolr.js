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
                {name: 'Originator', type: 'string'},
                {name: 'Location', type: 'string'},
                {name: 'LayerId', type: 'string'},
                {name: 'ContentDate', type: 'string'},
                {name: 'Availability', type: 'string'},
                {name: 'Abstract', type: 'string'}
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

                $(row).on('dblclick', function(){
                    self.rowDoubleClick(index);
                });
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
            GeoNode.queryTerms.rows = 500;
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

        // Remove any Originator filter if there
        for(var i=0;i<GeoNode.queryTerms.fq.length;i++){
            if(GeoNode.queryTerms.fq[i].indexOf('Originator') > -1){
                GeoNode.queryTerms.fq.splice(i, 1);
            }
        };
        if (this.originatorInput.getValue() !== ''){
            GeoNode.queryTerms.fq.push('Originator:' + this.originatorInput.getValue());
        }

        // Remove any DataType filter if there
        for(var i=0;i<GeoNode.queryTerms.fq.length;i++){
            if(GeoNode.queryTerms.fq[i].indexOf('DataType') > -1){
                GeoNode.queryTerms.fq.splice(i, 1);
            }
        };
        var datatypes = this.dataTypeInput.getValue().inputValue;
        if(datatypes !== ''){
            GeoNode.queryTerms.fq.push(datatypes);
        };

        // if (datatypes.length > 0 && datatypes[0].name != ''){
        //     var string = '';
        //     for(var i=0;i<datatypes.length;i++){
        //         string += datatypes[i].name + ' OR ';
        //     }
        //     string = string.slice(0, -4);
        //     GeoNode.queryTerms.fq.push(string);
        // }

        // Remove any date filter if there
        for(var i=0;i<GeoNode.queryTerms.fq.length;i++){
            if(GeoNode.queryTerms.fq[i].indexOf('ContentDate') > -1){
                GeoNode.queryTerms.fq.splice(i, 1);
            }
        };
        var dates = this.dateInput.getDateValues();
        if(dates){
            GeoNode.queryTerms.fq.push("ContentDate:" + this.dateInput.getDateValues());
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
        var controls_el = el.query('.search-controls')[0];

        //var expander = new GeoNode.SearchTableRowExpander({fetchURL: this.layerDetailURL});

        tableCfg = {
            store: this.searchStore,
            viewConfig: {
                autoFill: true,
                forceFit: true,
                emptyText: this.noResultsText
            },
            renderTo: 'search_results',
            height: 440,
            width: 310
        };

        var unviewableTooltip = this.unviewableTooltip;
        var remoteTooltip = this.remoteTooltip;

        var columns = [
            {
                header: this.titleHeaderText,
                dataIndex: 'LayerDisplayName',
                id: 'title',
                sortable: true,
                sortBy: 'LayerDisplayName',
                renderer: function(value, metadata, record, rowIndex, colIndex, store){
                    metadata.attr = 'ext:qtip="' + record.get('Abstract') + '"';
                    return value;
                }
            },
            {
                header: this.originatorText,
                dataIndex: 'Originator',
                id: 'originator',
                sortable: true
            },
            {
                header: 'Date',
                id: 'date',
                sortable: true,
                dataIndex: 'ContentDate',
                sortBy: 'ContentDate',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var date = new Date(record.get('ContentDate'));
                    return date.getFullYear();
                }
            },
            {
                header: 'Show',
                id: 'show',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    return '<input type="checkbox"/>';
                },
                listeners: {
                    click: function(scope, grid, rowIndex, e){
                        var record = grid.getStore().getAt(rowIndex);
                        if(e.target.checked){
                            self.heatmap.bbox_widget.viewer.fireEvent('showLayer',
                                self.getlayerTypename(record));
                        }else{
                            self.heatmap.bbox_widget.viewer.fireEvent('hideLayer',
                                self.getlayerTypename(record));
                        }

                    }
                }
            }
        ];

        if (this.trackSelection == true) {
            sm = new Ext.grid.CheckboxSelectionModel({
                checkOnly: true
            });
            sm.header = 'Select';

            this.dataCart = new GeoNode.DataCartStore({selModel: sm});
            columns.push(sm);
            tableCfg.selModel = sm;
        }

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
                        width: 150
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
                        width: 150
        });

        this.dataTypeInput = new Ext.form.RadioGroup({
            id: 'dataTypes',
            fieldLabel: 'Data Type',
            items: [
                {boxLabel: 'All Layers', name: 'datatypes', inputValue: '', checked: true},
                {boxLabel: 'WM Layers', name: 'datatypes', inputValue: 'DataType:Polygon OR DataType:Raster'},
                {boxLabel: 'WM Collections', name: 'datatypes', inputValue: 'DataType:RESTServices OR DataType:WMSServices'}
            ],
            listeners:{
                change: function(scope, checked){
                    self.updateQuery();
                }
            }
        });


        var dateStartTextField = new Ext.form.TextField({
            name: 'startDate',
            width: 110,
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
            width: 110,
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
            items: [new Ext.form.Label({text: 'From'}), dateStartTextField, new Ext.form.Label({text: 'to'}), dateEndTextField],
            layout: 'fit'
        });

        this.dateInput = new GeoNode.TimeSlider();


        //Set initial dates from the max and min dates from the server
        // function setInitialDates(){
        //     $.ajax({
        //         method: 'GET',
        //         jsonp: "json.wrf",
        //         dataType: "jsonp",
        //         url: 'http://54.83.116.189:8983/solr/wmdata/select?q=*&rows=1&sort=ContentDate asc&fl=ContentDate&wt=json',
        //         success: function(response_asc){
        //             $.ajax({
        //                 method: 'GET',
        //                 jsonp: "json.wrf",
        //                 dataType: "jsonp",
        //                 url: 'http://54.83.116.189:8983/solr/wmdata/select?q=*&rows=1&sort=ContentDate desc&fl=ContentDate&wt=json',
        //                 success: function(response_desc){
        //                     var startdate =  new Date(response_asc.response.docs[0].ContentDate);
        //                     var enddate = new Date(response_desc.response.docs[0].ContentDate);
        //                     self.dateInput.setMinValue(startdate.getFullYear());
        //                     self.dateInput.setMaxValue(enddate.getFullYear());
        //                     self.dateInput.setValue(0, startdate.getFullYear());
        //                     self.dateInput.setValue(1, enddate.getFullYear());
        //                 }
        //             })
        //         }
        //     })
        // };
        // setInitialDates();

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
            text: this.searchButtonText
        });
        searchButton.on('click', this.updateQuery, this);

        var searchForm = new Ext.Panel({
             width: '100%',
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
                    this.originatorInput,
                    searchButton
                ],
                colspan: 3
            },{
                items: [this.dataTypeInput],
                colspan: 3
            },{
                items: [this.dateLabelPanel, this.dateInput],
                colspan: 3
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
        bbox.south = element.data.MinY
        bbox.north = element.data.MaxY
        bbox.west = element.data.MinX
        bbox.east = element.data.MaxX
        return bbox
    },

    hideBounds : function() {
        this.heatmap.bbox_widget.viewer.fireEvent("hideBBox");
    },

    showPreviewLayer: function(element){
        var typename = this.getlayerTypename(element);
        var bbox = this.getLayerBounds(element);
        bbox = [bbox.west, bbox.south, bbox.east, bbox.north];
        this.heatmap.bbox_widget.viewer.fireEvent("showPreviewLayer", typename, bbox);
    },

    hidePreviewLayer: function(){
        this.heatmap.bbox_widget.viewer.fireEvent("hidePreviewLayer");
    },

    getlayerTypename: function(record){
        var layer_detail = JSON.parse(record.data.Location)['layerInfoPage'];
        var typename = layer_detail.split('/')[2];
        return decodeURIComponent(decodeURIComponent(typename));
    },

    rowDoubleClick: function(index){
        var record = this.table.getStore().getAt(index);
        this.heatmap.bbox_widget.viewer.fireEvent("zoomToRecord", record);
    }
});
