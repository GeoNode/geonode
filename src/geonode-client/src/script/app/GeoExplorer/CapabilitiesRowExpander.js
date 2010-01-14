Ext.namespace("GeoExplorer");

GeoExplorer.CapabilitiesRowExpander = Ext.extend(Ext.grid.RowExpander, {

    ows: null,

    abstractText: "UT:Abstract:",
    attributionEmptyText: "UT: No attribution information is provided for this layer.",
    attributionText: "UT:Provided by:",
    downloadText : "UT:Download:",
    keywordEmptyText: "UT: No keywords are listed for this layer.",
    keywordText: "UT:Keywords:",
    metadataEmptyText: 'UT: No metadata URLs are defined for this layer.',
    metadataText: "UT:Metadata Links:",

    constructor: function (config) {
        config.tpl = new Ext.Template('<p><b>' + this.abstractText + '</b> {abstract}</p>' +
            '<p><b>' + this.attributionText + '</b> {attribution:this.attributionLink}</p>'  +
            '<p><b>' + this.metadataText + '</b> {metadataURLs:this.metadataLinks}</p>'  +
            '<p><b>' + this.keywordText + '</b> {keywords:this.keywordList}</p>'  +
            '<p><b>' + this.downloadText + '</b> ' +
            '<a class="download pdf" href="{name:this.pdfUrl}">PDF</a>, ' +
            '<a class="download kml" href="{name:this.kmlUrl}">KML</a>, ' +
            '<a class="download geotiff" href="{name:this.geoTiffUrl}">GeoTIFF</a>' +
            '<span class="{owsType:this.showWFS}">, '  +
                '<a class="download shp" href="{name:this.shpUrl}">SHP (ZIP)</a>'  +
            '</span>' +
            '</p>');

        var expander, templateLib;
        expander = this;
        this.ows = config.ows;
        templateLib = Ext.apply({ows: function () {
            return expander.ows;
        }}, this.templateLibrary);
        templateLib.metadataEmptyText = this.metadataEmptyText;
        templateLib.keywordEmptyText = this.keywordEmptyText;
        templateLib.attributionEmptyText = this.attributionEmptyText;

        Ext.apply(config.tpl, templateLib);

        GeoExplorer.CapabilitiesRowExpander.superclass.constructor.call(this, config);
    },

    templateLibrary: {
        wmsParams: function (name, values, aspect) {
            // TODO: figure out a good default size and make sure we set the bounds properly.
            aspect = aspect || (8.5 / 11);

            var dx, dy, dataAspect, widthAdjust, heightAdjust;

            dx = values.llbbox[2] - values.llbbox[0];
            dy = values.llbbox[3] - values.llbbox[1];
            dataAspect = dx / dy;

            widthAdjust = 1;
            heightAdjust = 1;

            if (dataAspect > aspect) {
                heightAdjust = dataAspect / aspect;
            } else {
                widthAdjust = aspect / dataAspect;
            }

            return {
                service: "wms",
                request: "GetMap",
                bbox: this.adjustBounds(widthAdjust, heightAdjust, values.llbbox).toString(),
                layers: name,
                srs: "EPSG:4326",
                width: 425, // = 8.5 * 50
                height: 550 // = 11 * 50
            };
        },

        adjustBounds: function (widthAdjust, heightAdjust, bbox) {
            var dx, dy, midx, midy;
            dx = bbox[2] - bbox[0];
            dy = bbox[3] - bbox[1];

            midx = (bbox[2] + bbox[0]) / 2;
            midy = (bbox[3] + bbox[1]) / 2;

            return [midx - (widthAdjust * dx) / 2, midy - (heightAdjust * dy) / 2,
                    midx + (widthAdjust * dx) / 2, midy + (heightAdjust * dy) / 2];
        },

        wfsParams: function (name, values) {
            return {
                service: "wfs",
                request: "GetFeature",
                typeName: name
            };
        },

        showWFS: function (owsType, values) {
            return owsType === "WFS" ? "" : "nodisplay";
        },

        shpUrl: function (name, values) {
            // There's no official mimetype for "A ZIP archive containing a Shapefile and its 
            // associated metafiles" so we just use GeoServer's psuedo-type for it.
            var shpParams = Ext.apply(this.wfsParams(name, values), {outputFormat: 'SHAPE-ZIP'});
            return this.ows() + "?" + Ext.urlEncode(shpParams);
        },

        pdfUrl: function (name, values) {
            var pdfParams = Ext.apply(this.wmsParams(name, values), {format: 'application/pdf'});
            return this.ows() + "?" + Ext.urlEncode(pdfParams);
        },

        kmlUrl: function (name, values) {
            var kmlParams = Ext.apply(this.wmsParams(name, values), {
                format: 'application/vnd.google-earth.kmz+xml',
                height: 2048,
                width: 2048
            }, 1);
            return this.ows() + "?" + Ext.urlEncode(kmlParams);
        },

        geoTiffUrl: function (name, values) {
            var geoTiffParams = Ext.apply(this.wmsParams(name, values), 
                {format: "image/geotiff"});
            return this.ows() + "?" + Ext.urlEncode(geoTiffParams);
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
                    links.push("<a href=\"" + metadataURLs[i].href + "\"> " +
                        metadataURLs[i].type + "</a>");
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
            if (attribution == null || attribution.href == null) {
                return "<em>" + this.attributionEmptyText + "</em>";
            } else {
                return "<a href=\"" + attribution.href + "\"> " + attribution.title + "</a>";
            }
        }
    }
});
