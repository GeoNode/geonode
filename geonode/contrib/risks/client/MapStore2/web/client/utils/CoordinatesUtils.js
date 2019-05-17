/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const Proj4js = require('proj4');
const proj4 = Proj4js;
const assign = require('object-assign');
const {isArray, flattenDeep, chunk, cloneDeep} = require('lodash');
// Checks if `list` looks like a `[x, y]`.
function isXY(list) {
    return list.length >= 2 &&
        typeof list[0] === 'number' &&
        typeof list[1] === 'number';
}
function traverseCoords(coordinates, callback) {
    if (isXY(coordinates)) return callback(coordinates);
    return coordinates.map(function(coord) { return traverseCoords(coord, callback); });
}

function traverseGeoJson(geojson, leafCallback, nodeCallback) {
    if (geojson === null) return geojson;

    let r = cloneDeep(geojson);

    if (geojson.type === 'Feature') {
        r.geometry = traverseGeoJson(geojson.geometry, leafCallback, nodeCallback);
    } else if (geojson.type === 'FeatureCollection') {
        r.features = r.features.map(function(gj) { return traverseGeoJson(gj, leafCallback, nodeCallback); });
    } else if (geojson.type === 'GeometryCollection') {
        r.geometries = r.geometries.map(function(gj) { return traverseGeoJson(gj, leafCallback, nodeCallback); });
    } else {
        if (leafCallback) leafCallback(r);
    }

    if (nodeCallback) nodeCallback(r);

    return r;
}

function determineCrs(crs) {
    if (typeof crs === 'string' || crs instanceof String) {
        return Proj4js.defs(crs) ? new Proj4js.Proj(crs) : null;
    }
    return crs;
}

const CoordinatesUtils = {
    getUnits: function(projection) {
        const proj = new Proj4js.Proj(projection);
        return proj.units || 'degrees';
    },
    reproject: function(point, source, dest, normalize = true) {
        const sourceProj = Proj4js.defs(source) ? new Proj4js.Proj(source) : null;
        const destProj = Proj4js.defs(dest) ? new Proj4js.Proj(dest) : null;
        if (sourceProj && destProj) {
            let p = isArray(point) ? Proj4js.toPoint(point) : Proj4js.toPoint([point.x, point.y]);
            const transformed = assign({}, source === dest ? p : Proj4js.transform(sourceProj, destProj, p), {srs: dest});
            if (normalize) {
                return CoordinatesUtils.normalizePoint(transformed);
            }
            return transformed;
        }
        return null;
    },
    /**
     * Reprojects a geojson from a crs into another
     */
    reprojectGeoJson: function(geojson, fromParam = "EPSG:4326", toParam = "EPSG:4326") {
        let from = fromParam;
        let to = toParam;
        if (typeof from === 'string') {
            from = determineCrs(from);
        }
        if (typeof to === 'string') {
            to = determineCrs(to);
        }
        let transform = proj4(from, to);

        return traverseGeoJson(geojson, (gj) => {
            // No easy way to put correct CRS info into the GeoJSON,
            // and definitely wrong to keep the old, so delete it.
            if (gj.crs) {
                delete gj.crs;
            }
            gj.coordinates = traverseCoords(gj.coordinates, (xy) => {
                return transform.forward(xy);
            });
        }, (gj) => {
            if (gj.bbox) {
                // A bbox can't easily be reprojected, just reprojecting
                // the min/max coords definitely will not work since
                // the transform is not linear (in the general case).
                // Workaround is to just re-compute the bbox after the
                // transform.
                gj.bbox = (() => {
                    let min = [Number.MAX_VALUE, Number.MAX_VALUE];
                    let max = [-Number.MAX_VALUE, -Number.MAX_VALUE];
                    traverseGeoJson(gj, function(_gj) {
                        traverseCoords(_gj.coordinates, function(xy) {
                            min[0] = Math.min(min[0], xy[0]);
                            min[1] = Math.min(min[1], xy[1]);
                            max[0] = Math.max(max[0], xy[0]);
                            max[1] = Math.max(max[1], xy[1]);
                        });
                    });
                    return [min[0], min[1], max[0], max[1]];
                })();
            }
        });
    },
    normalizePoint: function(point) {
        return {
            x: point.x || 0.0,
            y: point.y || 0.0,
            srs: point.srs || 'EPSG:4326'
        };
    },
    /**
     * Reprojects a bounding box.
     *
     * @param bbox {array} [minx, miny, maxx, maxy]
     * @param source {string} SRS of the given bbox
     * @param dest {string} SRS of the returned bbox
     *
     * @return {array} [minx, miny, maxx, maxy]
     */
    reprojectBbox: function(bbox, source, dest, normalize = true) {
        let points;
        if (isArray(bbox)) {
            points = {
                sw: [bbox[0], bbox[1]],
                ne: [bbox[2], bbox[3]]
            };
        } else {
            points = {
                sw: [bbox.minx, bbox.miny],
                ne: [bbox.maxx, bbox.maxy]
            };
        }
        let projPoints = [];
        for (let p in points) {
            if (points.hasOwnProperty(p)) {
                const projected = CoordinatesUtils.reproject(points[p], source, dest, normalize);
                if (projected) {
                    let {x, y} = projected;
                    projPoints.push(x);
                    projPoints.push(y);
                } else {
                    return null;
                }
            }
        }
        return projPoints;
    },
    getCompatibleSRS(srs, allowedSRS) {
        if (srs === 'EPSG:900913' && !allowedSRS['EPSG:900913'] && allowedSRS['EPSG:3857']) {
            return 'EPSG:3857';
        }
        if (srs === 'EPSG:3857' && !allowedSRS['EPSG:3857'] && allowedSRS['EPSG:900913']) {
            return 'EPSG:900913';
        }
        return srs;
    },
    getEquivalentSRS(srs) {
        if (srs === 'EPSG:900913' || srs === 'EPSG:3857') {
            return ['EPSG:3857', 'EPSG:900913'];
        }
        return [srs];
    },
    getEPSGCode(code) {
        if (code.indexOf(':') !== -1) {
            return 'EPSG:' + code.substring(code.lastIndexOf(':') + 1);
        }
        return code;
    },
    normalizeSRS: function(srs, allowedSRS) {
        const result = (srs === 'EPSG:900913' ? 'EPSG:3857' : srs);
        if (allowedSRS && !allowedSRS[result]) {
            return CoordinatesUtils.getCompatibleSRS(result, allowedSRS);
        }
        return result;
    },
    isAllowedSRS(srs, allowedSRS) {
        return allowedSRS[CoordinatesUtils.getCompatibleSRS(srs, allowedSRS)];
    },
    getAvailableCRS: function() {
        let crsList = {};
        for (let a in Proj4js.defs) {
            if (Proj4js.defs.hasOwnProperty(a)) {
                crsList[a] = {label: a};
            }
        }
        return crsList;
    },
    calculateAzimuth: function(p1, p2, pj) {
        var p1proj = CoordinatesUtils.reproject(p1, pj, 'EPSG:4326');
        var p2proj = CoordinatesUtils.reproject(p2, pj, 'EPSG:4326');
        var lon1 = p1proj.x * Math.PI / 180.0;
        var lat1 = p1proj.y * Math.PI / 180.0;
        var lon2 = p2proj.x * Math.PI / 180.0;
        var lat2 = p2proj.y * Math.PI / 180.0;
        var dLon = lon2 - lon1;
        var y = Math.sin(dLon) * Math.cos(lat2);
        var x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);

        var azimuth = (((Math.atan2(y, x) * 180.0 / Math.PI) + 360 ) % 360 );

        return azimuth;
    },
    /**
     * Extend an extent given another one
     *
     * @param extent1 {array} [minx, miny, maxx, maxy]
     * @param extent2 {array} [minx, miny, maxx, maxy]
     *
     * @return {array} [minx, miny, maxx, maxy]
     */
    extendExtent: function(extent1, extent2) {
        let newExtent = extent1.slice();
        if (extent2[0] < extent1[0]) {
            newExtent[0] = extent2[0];
        }
        if (extent2[2] > extent1[2]) {
            newExtent[2] = extent2[2];
        }
        if (extent2[1] < extent1[1]) {
            newExtent[1] = extent2[1];
        }
        if (extent2[3] > extent1[3]) {
            newExtent[3] = extent2[3];
        }
        return newExtent;
    },
    /**
     * Calculates the extent for the geoJSON passed. It used a small buffer for points.
     * Like turf/bbox but works only with simple geometries.
     * @deprecated  We may replace it with turf/bbox + turf/buffer in the future, so using it with geometry is discouraged
     * @param {geoJSON|geometry} GeoJSON or geometry
     * @return {array} extent of the geoJSON
     */
    getGeoJSONExtent: function(geoJSON) {
        let newExtent = [Infinity, Infinity, -Infinity, -Infinity];
        const reduceCollectionExtent = (extent, collectionElement) => {
            let ext = this.getGeoJSONExtent(collectionElement);
            if (this.isValidExtent(ext)) {
                return this.extendExtent(ext, extent);
            }
        };
        if (geoJSON.coordinates) {
            if (geoJSON.type === "Point") {
                let point = geoJSON.coordinates;
                newExtent[0] = point[0] - point[0] * 0.01;
                newExtent[1] = point[1] - point[1] * 0.01;
                newExtent[2] = point[0] + point[0] * 0.01;
                newExtent[3] = point[1] + point[1] * 0.01;
            }
            // other kinds of geometry
            const flatCoordinates = chunk(flattenDeep(geoJSON.coordinates), 2);
            return flatCoordinates.reduce((extent, point) => {
                return [
                    (point[0] < extent[0]) ? point[0] : extent[0],
                    (point[1] < extent[1]) ? point[1] : extent[1],
                    (point[0] > extent[2]) ? point[0] : extent[2],
                    (point[1] > extent[3]) ? point[1] : extent[3]
                ];
            }, newExtent);

        } else if (geoJSON.type === "GeometryCollection") {
            let geometries = geoJSON.geometries;
            return geometries.reduce(reduceCollectionExtent, newExtent);
        } else if (geoJSON.type) {
            if (geoJSON.type === "FeatureCollection") {
                return geoJSON.features.reduce(reduceCollectionExtent, newExtent);
            } else if (geoJSON.type === "Feature" && geoJSON.geometry) {
                return this.getGeoJSONExtent(geoJSON.geometry);
            }
        }

        return newExtent;
    },
    /**
     * Check extent validity
     *
     * @param extent {array} [minx, miny, maxx, maxy]
     *
     * @return {bool}
     */
    isValidExtent: function(extent) {
        return !(
            extent.indexOf(Infinity) !== -1 || extent.indexOf(-Infinity) !== -1 ||
            extent[0] > extent[2] || extent[1] > extent[3]
        );
    },
    calculateCircleCoordinates: function(center, radius, sides, rotation) {
        let angle = Math.PI * ((1 / sides) - (1 / 2));

        if (rotation) {
            angle += (rotation / 180) * Math.PI;
        }

        let rotatedAngle; let x; let y;
        let points = [[]];
        for (let i = 0; i < sides; i++) {
            rotatedAngle = angle + (i * 2 * Math.PI / sides);
            x = center.x + (radius * Math.cos(rotatedAngle));
            y = center.y + (radius * Math.sin(rotatedAngle));
            points[0].push([x, y]);
        }

        points[0].push(points[0][0]);
        return points;
    }
};

module.exports = CoordinatesUtils;
