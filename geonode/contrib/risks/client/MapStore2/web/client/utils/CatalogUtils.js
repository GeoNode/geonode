/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const assign = require('object-assign');
const {head, isArray, isString} = require('lodash');
const urlUtil = require('url');
const CoordinatesUtils = require('./CoordinatesUtils');
const {castArray} = require('lodash');

const getWMSBBox = (record) => {
    let layer = record;
    let bbox = (layer.EX_GeographicBoundingBox || (layer.LatLonBoundingBox && layer.LatLonBoundingBox.$));
    while (!bbox && layer.Layer && layer.Layer.length) {
        layer = layer.Layer[0];
        bbox = (layer.EX_GeographicBoundingBox || (layer.LatLonBoundingBox && layer.LatLonBoundingBox.$));
    }
    if (!bbox) {
        bbox = {
            westBoundLongitude: -180.0,
            southBoundLatitude: -90.0,
            eastBoundLongitude: 180.0,
            northBoundLatitude: 90.0
        };
    }
    return bbox;
};
const getBaseCatalogUrl = (url) => {
    return url && url.replace(/\/csw$/, "/");
};

const getWMTSBBox = (record) => {
    let layer = record;
    let bbox = (layer["ows:WGS84BoundingBox"]);
    if (!bbox) {
        bbox = {
            "ows:LowerCorner": "-180.0 -90.0",
            "ows:UpperCorner": "180.0 90.0"
        };
    }
    return bbox;
};

const converters = {
    csw: (records, options) => {
        let result = records;
        // let searchOptions = catalog.searchOptions;
        if (result && result.records) {
            return result.records.map((record) => {
                let dc = record.dc;
                let thumbURL;
                let wms;
                // look in URI objects for wms and thumbnail
                if (dc && dc.URI) {
                    const URI = isArray(dc.URI) ? dc.URI : (dc.URI && [dc.URI] || []);
                    let thumb = head([].filter.call(URI, (uri) => {return uri.name === "thumbnail"; }) );
                    thumbURL = thumb ? thumb.value : null;
                    wms = head([].filter.call(URI, (uri) => { return uri.protocol === "OGC:WMS-1.1.1-http-get-map"; }));
                }
                // look in references objects
                if (!wms && dc.references && dc.references.length) {
                    let refs = Array.isArray(dc.references) ? dc.references : [dc.references];
                    wms = head([].filter.call( refs, (ref) => { return ref.scheme === "OGC:WMS-1.1.1-http-get-map" || ref.scheme === "OGC:WMS"; }));
                    if (wms) {
                        let urlObj = urlUtil.parse(wms.value, true);
                        let layerName = urlObj.query && urlObj.query.layers;
                        wms = assign({}, wms, {name: layerName} );
                    }
                }
                if (!thumbURL && dc.references) {
                    let refs = Array.isArray(dc.references) ? dc.references : [dc.references];
                    let thumb = head([].filter.call( refs, (ref) => { return ref.scheme === "WWW:LINK-1.0-http--image-thumbnail" || ref.scheme === "thumbnail"; }));
                    if (thumb) {
                        thumbURL = thumb.value;
                    }
                }

                let references = [];

                // extract get capabilities references and add them to the final references
                if (dc.references) {
                    // make sure we have an array of references
                    let rawReferences = Array.isArray(dc.references) ? dc.references : [dc.references];
                    rawReferences.filter((reference) => {
                        // filter all references that correspond to a get capabilities reference
                        return reference.scheme.indexOf("http-get-capabilities") > -1;
                    }).forEach((reference) => {
                        // a get capabilities reference should be absolute and filter by the layer name
                        let referenceUrl = reference.value.indexOf("http") === 0 ? reference.value
                            : options.catalogURL + "/" + reference.value;
                        // add the references to the final list
                        references.push({
                            type: reference.scheme,
                            url: referenceUrl
                        });
                    });
                }

                if (wms && wms.name) {
                    let absolute = (wms.value.indexOf("http") === 0);
                    if (!absolute) {
                        assign({}, wms, {value: options.catalogURL + "/" + wms.value} );
                    }
                    let wmsReference = {
                        type: wms.protocol || wms.scheme,
                        url: wms.value,
                        SRS: [],
                        params: {
                            name: wms.name
                        }
                    };
                    references.push(wmsReference);
                }
                if (thumbURL) {
                    let absolute = (thumbURL.indexOf("http") === 0);
                    if (!absolute) {
                        thumbURL = (getBaseCatalogUrl(options.url) || "") + thumbURL;
                    }
                }
                // create the references array (now only wms is supported)

                // setup the final record object
                return {
                    title: isString(dc.title) && dc.title || '',
                    description: isString(dc.abstract) && dc.abstract || '',
                    identifier: isString(dc.identifier) && dc.identifier || '',
                    thumbnail: thumbURL,
                    tags: isString(dc.subject) && dc.subject || '',
                    boundingBox: record.boundingBox,
                    references: references
                };
            });
        }
    },
    wms: (records, options) => {
        if (records && records.records) {
            return records.records.map((record) => {
                const bbox = getWMSBBox(record);
                return {
                title: record.Title || record.Name,
                description: record.Abstract || record.Title || record.Name,
                identifier: record.Name,
                tags: "",
                capabilities: record,
                service: records.service,
                boundingBox: {
                    extent: [
                            bbox.westBoundLongitude || bbox.minx,
                            bbox.southBoundLatitude || bbox.miny,
                            bbox.eastBoundLongitude || bbox.maxx,
                            bbox.northBoundLatitude || bbox.maxy
                    ],
                    crs: "EPSG:4326"
                },
                references: [{
                    type: "OGC:WMS",
                    url: options.url,
                    SRS: (record.SRS && (isArray(record.SRS) ? record.SRS : [record.SRS])) || [],
                    params: {
                        name: record.Name
                    }
                }]
                };
            });
        }
    },
    wmts: (records, options) => {
        if (records && records.records) {
            return records.records.map((record) => {
                const bbox = getWMTSBBox(record);
                return {
                title: record["ows:Title"] || record["ows:Identifier"],
                description: record["ows:Abstract"] || record["ows:Title"] || record["ows:Identifier"],
                identifier: record["ows:Identifier"],
                tags: "",
                tileMatrixSet: record.TileMatrixSet,
                matrixIds: castArray(record.TileMatrixSetLink).reduce((previous, current) => {
                    const tileMatrix = head(record.TileMatrixSet.filter((matrix) => matrix["ows:Identifier"] === current.TileMatrixSet));
                    const tileMatrixSRS = CoordinatesUtils.getEPSGCode(tileMatrix["ows:SupportedCRS"]);
                    const levels = current.TileMatrixSetLimits && current.TileMatrixSetLimits.TileMatrixLimits.map((limit) => ({
                        identifier: limit.TileMatrix,
                        ranges: {
                            cols: {
                                min: limit.MinTileCol,
                                max: limit.MaxTileCol
                            },
                            rows: {
                                min: limit.MinTileRow,
                                max: limit.MaxTileRow
                            }
                        }
                    })) || tileMatrix.TileMatrix.map((matrix) => ({
                        identifier: matrix["ows:Identifier"]
                    }));

                    return assign(previous, {
                        [tileMatrix["ows:Identifier"]]: levels,
                        [tileMatrixSRS]: levels
                    });
                }, {}),
                TileMatrixSetLink: castArray(record.TileMatrixSetLink),
                boundingBox: {
                    extent: [
                            bbox["ows:LowerCorner"].split(" ")[0],
                            bbox["ows:LowerCorner"].split(" ")[1],
                            bbox["ows:UpperCorner"].split(" ")[0],
                            bbox["ows:UpperCorner"].split(" ")[1]
                    ],
                    crs: "EPSG:4326"
                },
                references: [{
                    type: "OGC:WMTS",
                    url: record.GetTileUrl || options.url,
                    SRS: record.SRS || [],
                    params: {
                        name: record["ows:Identifier"]
                    }
                }]
                };
            });
        }
    }
};

const CatalogUtils = {

    getCatalogRecords: (format, records, options) => {
        return converters[format] && converters[format](records, options) || null;
    }
};


module.exports = CatalogUtils;
