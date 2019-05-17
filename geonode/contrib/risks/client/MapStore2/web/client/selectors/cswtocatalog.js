/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const assign = require('object-assign');
const {head} = require('lodash');
const urlUtil = require('url');


const getBaseCatalogUrl = (url) => {
    return url && url.substring(0, url.lastIndexOf("/"));
};
/**
 * Parses a csw object and returns an object with a common form.
 * records:
 *
 */
const cswToCatalogSelector = (catalog) => {
    let result = catalog.result;
    let searchOptions = catalog.searchOptions;
    if (result && result.records) {
        return result.records.map((record) => {
            let dc = record.dc;
            let thumbURL;
            let wms;
            // look in URI objects for wms and thumbnail
            if (dc && dc.URI) {
                let thumb = head([].filter.call(dc.URI, (uri) => {return uri.name === "thumbnail"; }) );
                thumbURL = thumb ? thumb.value : null;
                wms = head([].filter.call(dc.URI, (uri) => { return uri.protocol === "OGC:WMS-1.1.1-http-get-map"; }));
            }
            // look in references objects
            if (!wms && dc.references) {
                let refs = Array.isArray(dc.references) ? dc.references : [dc.references];
                wms = head([].filter.call( refs, (ref) => { return ref.scheme === "OGC:WMS-1.1.1-http-get-map" || ref.scheme === "OGC:WMS"; }));
                let urlObj = urlUtil.parse(wms.value, true);
                let layerName = urlObj.query && urlObj.query.layers;
                wms = assign({}, wms, {name: layerName} );
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
                        : getBaseCatalogUrl(searchOptions.catalogURL || searchOptions.url) + reference.value;
                    // add the references to the final list
                    references.push({
                        type: reference.scheme,
                        url: referenceUrl
                    });
                });
            }

            /*
            References have this form:
                {
                    type: "OGC:WMS",
                    url: "http:....",
                    params: {
                        name: "topp:states" // type specific
                    }
                }
            */
            if (wms) {
                let absolute = (wms.value.indexOf("http") === 0);
                if (!absolute) {
                    assign({}, wms, {value: getBaseCatalogUrl(searchOptions.catalogURL || searchOptions.url) + wms.value} );
                }
                let wmsReference = {
                    type: wms.protocol || wms.scheme,
                    url: wms.value,
                    params: {
                        name: wms.name
                    }
                };
                references.push(wmsReference);
            }
            if (thumbURL) {
                let absolute = (thumbURL.indexOf("http") === 0);
                if (!absolute) {
                    thumbURL = getBaseCatalogUrl(searchOptions.catalogURL || searchOptions.url) + thumbURL;
                }
            }
            // create the references array (now only wms is supported)

            // setup the final record object
            return {
                title: dc.title,
                description: dc.abstract,
                identifier: dc.identifier,
                thumbnail: thumbURL,
                tags: dc.subject,
                boundingBox: record.boundingBox,
                references: references
            };
        });
    }
};
module.exports = {cswToCatalogSelector};
