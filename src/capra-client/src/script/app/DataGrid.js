Ext.namespace("capra");

capra.DataGrid = Ext.extend(Ext.util.Observable, {
    dataTitleHeaderText: "UT:Title",
    dataNameHeaderText: "UT:Name",
    dataDetailText: "UT: More information about this layer",
    layerTitleSuffix: " Layers (UT)",
    uncategorizedLabel: "UT: Uncategorized",

    /**
     * A store containing the WMS capabilities for the server
     */
    capabilities: null, 

    constructor: function(config) {
        Ext.apply(this, config);

        if (this.proxy) { // Forward GeoNode proxy settings to OpenLayers
            OpenLayers.ProxyHost = this.proxy;
        }

        var url = this.owsURL({
            "request": "GetCapabilities",
            "service": "WMS"
        });

        // TODO: Review this. Do we really need to specify all the fields?
        this.capabilities = new GeoExt.data.WMSCapabilitiesStore({
            url: url,
            fields: [
                {name: "name", type: "string"},
                {name: "abstract", type: "string"},
                {name: "queryable", type: "boolean"},
                {name: "formats"},
                {name: "styles"},
                {name: "llbbox"},
                {name: "minScale"},
                {name: "maxScale"},
                {name: "prefix"},
                {name: "attribution"},
                {name: "keywords"},
                {name: "metadataURLs"},
                {name: "owsType"}
            ]
        });

        Ext.util.Observable.prototype.constructor.apply(this, arguments);
        this.loadData();
    },

    owsURL: function(params) {
        var url = this.ows + '?' + Ext.urlEncode(params);
        if (this.proxy) {
            url = this.proxy + '?' + Ext.urlEncode({ 'url': url });
        }
        return url;
    },

    loadData: function() {
        gxp.util.dispatch([
                function(done) {
                    this.capabilities.load({
                        callback: done 
                    }); 
                }
            ],
            function() { this.doLayout(); },
            this
        );
    },

    doLayout: function() {
        var me = this; // alias for i18n retrieval
        var categories = this.categories || {};
        var clusters = {};
        var clusternames = [];
        var expanderTemplate = 
            '<p><b>' + GeoExplorer.CapabilitiesRowExpander.prototype.abstractText + '</b> {abstract}</p>' +
            '<p><b>' + GeoExplorer.CapabilitiesRowExpander.prototype.attributionText + '</b> {attribution:this.attributionLink}</p>'  +
            '<p><b>' + GeoExplorer.CapabilitiesRowExpander.prototype.metadataText + '</b> {metadataURLs:this.metadataLinks}</p>'  +
            '<p><b>' + GeoExplorer.CapabilitiesRowExpander.prototype.keywordText + '</b> {keywords:this.keywordList}</p>'  +
            '<p><b>' + GeoExplorer.CapabilitiesRowExpander.prototype.downloadText + '</b> ' +
            '<a class="download pdf" href="{name:this.pdfUrl}">PDF</a>, ' +
            '<a class="download kml" href="{name:this.kmlUrl}">KML</a>, ' +
            '<a class="download geotiff" href="{name:this.geoTiffUrl}">GeoTIFF</a>' +
            '<span class="{owsType:this.showWFS}">, '  +
            '<a class="download shp" href="{name:this.shpUrl}">SHP (ZIP)</a>'  +
            '</span>' +
            '</p>' +
            '<p><a href="/data/{name}">' + this.dataDetailText + '</a></p>';


        function toTitleCase(s) {
            return s.replace(/\b[a-z]/g, function(c) {
                return c.toUpperCase()
            });
        }

        function createGrid(header, store) {
            var expander = new GeoExplorer.CapabilitiesRowExpander({
                ows: this.ows,
                tpl: new Ext.Template(expanderTemplate)
            });
            return new Ext.grid.GridPanel({
                store: store,
                title: header,
                plugins: [expander],
                colModel: new Ext.grid.ColumnModel([
                    expander, 
                    {
                        id: "title", 
                        header: me.dataTitleHeaderText,
                        dataIndex: "title",
                        sortable: true,
                        renderer: function(value,metaData,record) { 
                            console.log(record);
			    return "<a href='/data/" + record.get('name') +  "'>" + value + "</a>" ; }
                    }, {
                        header: me.dataNameHeaderText,
                        dataIndex: "name", 
                        width: 180,
                        sortable: true
                    }
                ]),
                viewConfig: { autoFill: true },
                sm: new Ext.grid.RowSelectionModel({singleSelect:true}),
                height: 200
            });
        }

        this.capabilities.filterBy(function(rec) {
            var name = rec.get('name');
            if (name in categories) {
                var categoryName = categories[name];
                if (!(categoryName in clusters)) {
                    clusternames.push(categoryName);
                    clusters[categoryName] = new Ext.data.Store({
                        recordType: this.capabilities.recordType
                    });
                }
                clusters[categoryName].add(rec);
                return false;
            } else {
                return true;
            }
        }, this);

        var grids = [];
        for (var i = 0, len = clusternames.length; i < len; i++) {
            var name = clusternames[i];
            var header = toTitleCase(name) + this.layerTitleSuffix;
            var grid = createGrid(header, clusters[name])
            grids.push(grid, new Ext.Panel({border: false, height: 20}));
        }

        if (this.capabilities.getCount() > 0) {
            var name = this.uncategorizedLabel;
            var header = toTitleCase(name) + this.layerTitleSuffix;
            var grid = createGrid(header, this.capabilities);
            grids.push(grid, new Ext.Panel({border: false, height: 20}));
        }

        var panel = new Ext.Panel({
            items: grids,
            border: false,
            renderTo: this.renderTo
        });
    }
});
