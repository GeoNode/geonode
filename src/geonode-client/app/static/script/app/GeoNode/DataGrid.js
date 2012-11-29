Ext.namespace("GeoNode");
GeoNode.DataGrid = Ext.extend(Ext.util.Observable, {
    dataTitleHeaderText : "UT:Title",
    dataNameHeaderText : "UT:Name",
    dataDetailText: 'UT: Click here for more information about this layer.',

    constructor: function(config) {
        Ext.apply(this, config);
        this.loadData();
    },

    owsURL: function(params) {
        var url = this.ows + '?' + Ext.urlEncode(params);
        if (this.proxy) {
            url = this.proxy + '?' + Ext.urlEncode({ "url": url });
        }
        return url;
    },

    loadData: function() {
        var url = this.owsURL({
            'service': 'WMS',
            'request': 'GetCapabilities'
        });

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

        gxp.util.dispatch([
                function(done) {
                    this.capabilities.load({
                        callback: done,
                        scope: this
                    });
                }
            ], 
            this.doLayout,
            this
        );
    },

    doLayout: function() {
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

        var expander = new GeoExplorer.CapabilitiesRowExpander({
            tpl: new Ext.Template(expanderTemplate),
            ows: this.ows
        });

        new Ext.grid.GridPanel({
            store: this.capabilities, 
            plugins: [expander],
            columns: [
                expander,
                {
                    header: this.dataTitleHeaderText,
                    dataIndex: 'title'
                }, {
                    header: this.dataNameHeaderText,
                    dataIndex: 'name'
            }],
            viewConfig: {autoFill: true},
            height: 300,
            renderTo: this.renderTo
        })
    }
});
