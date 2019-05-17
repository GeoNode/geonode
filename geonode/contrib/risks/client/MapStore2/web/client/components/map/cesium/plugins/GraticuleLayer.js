/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/cesium/Layers');
var Cesium = require('../../../../libs/cesium');
var assign = require('object-assign');

/**
 * Created by thomas on 27/01/14.
 // [source 07APR2015: http://pad.geocento.com/AddOns/Graticule.js]
 */

var Graticule = (function() {

    var mins = [
        Cesium.Math.toRadians(0.05),
        Cesium.Math.toRadians(0.1),
        Cesium.Math.toRadians(0.2),
        Cesium.Math.toRadians(0.5),
        Cesium.Math.toRadians(1.0),
        Cesium.Math.toRadians(2.0),
        Cesium.Math.toRadians(5.0),
        Cesium.Math.toRadians(10.0)
    ];

    function _(dsc, scene) {

        let description = dsc || {};

        this._tilingScheme = description.tilingScheme || new Cesium.GeographicTilingScheme();

        this._color = description.color &&
            new Cesium.Color(description.color[0], description.color[1], description.color[2], description.color[3]) ||
            new Cesium.Color(1.0, 1.0, 1.0, 0.4);

        this._tileWidth = description.tileWidth || 256;
        this._tileHeight = description.tileHeight || 256;

        this._ready = true;

        // default to decimal intervals
        this._sexagesimal = description.sexagesimal || false;
        this._numLines = description.numLines || 50;

        this._scene = scene;
        this._labels = new Cesium.LabelCollection();
        scene.primitives.add(this._labels);
        this._polylines = new Cesium.PolylineCollection();
        scene.primitives.add(this._polylines);
        this._ellipsoid = scene.globe.ellipsoid;

        let canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        this._canvas = canvas;

    }

    let definePropertyWorks = (function() {
        try {
            return 'x' in Object.defineProperty({}, 'x', {});
        } catch (e) {
            return false;
        }
    })();

    /**
     * Defines properties on an object, using Object.defineProperties if available,
     * otherwise returns the object unchanged.  This function should be used in
     * setup code to prevent errors from completely halting JavaScript execution
     * in legacy browsers.
     *
     * @private
     *
     * @exports defineProperties
     */
    let defineProperties = Object.defineProperties;
    if (!definePropertyWorks || !defineProperties) {
        defineProperties = function(o) {
            return o;
        };
    }

    defineProperties(_.prototype, {
        url: {
            get: function() {
                return undefined;
            }
        },

        proxy: {
            get: function() {
                return undefined;
            }
        },

        tileWidth: {
            get: function() {
                return this._tileWidth;
            }
        },

        tileHeight: {
            get: function() {
                return this._tileHeight;
            }
        },

        maximumLevel: {
            get: function() {
                return 18;
            }
        },

        minimumLevel: {
            get: function() {
                return 0;
            }
        },
        tilingScheme: {
            get: function() {
                return this._tilingScheme;
            }
        },
        rectangle: {
            get: function() {
                return this._tilingScheme.rectangle;
            }
        },
        tileDiscardPolicy: {
            get: function() {
                return undefined;
            }
        },
        errorEvent: {
            get: function() {
                return this._errorEvent;
            }
        },
        ready: {
            get: function() {
                return this._ready;
            }
        },
        credit: {
            get: function() {
                return this._credit;
            }
        },
        hasAlphaChannel: {
            get: function() {
                return true;
            }
        }
    });

    _.prototype.makeLabel = function(lng, lat, text, top) {
        this._labels.add({
            position: this._ellipsoid.cartographicToCartesian(new Cesium.Cartographic(lng, lat, 10.0)),
            text: text,
            font: 'normal',
            fillColor: this._color,
            outlineColor: this._color,
            style: Cesium.LabelStyle.FILL,
            pixelOffset: new Cesium.Cartesian2(5, top ? 5 : -5),
            eyeOffset: Cesium.Cartesian3.ZERO,
            horizontalOrigin: Cesium.HorizontalOrigin.LEFT,
            verticalOrigin: top ? Cesium.VerticalOrigin.BOTTOM : Cesium.VerticalOrigin.TOP,
            scale: 1.0
        });
    };

    _.prototype._drawGrid = function(extent) {

        if (this._currentExtent && this._currentExtent.equals(extent)) {
            return;
        }
        this._currentExtent = extent;

        this._polylines.removeAll();
        this._labels.removeAll();

        let dLat = 0;
        let dLng = 0;
        // get the nearest to the calculated value
        for (let index = 0; index < mins.length && dLat < ((extent.north - extent.south) / 10); index++) {
            dLat = mins[index];
        }
        for (let index = 0; index < mins.length && dLng < ((extent.east - extent.west) / 10); index++) {
            dLng = mins[index];
        }

        // round iteration limits to the computed grid interval
        let minLng = (extent.west < 0 ? Math.ceil(extent.west / dLng) : Math.floor(extent.west / dLng)) * dLng;
        let minLat = (extent.south < 0 ? Math.ceil(extent.south / dLat) : Math.floor(extent.south / dLat)) * dLat;
        let maxLng = (extent.east < 0 ? Math.ceil(extent.east / dLat) : Math.floor(extent.east / dLat)) * dLat;
        let maxLat = (extent.north < 0 ? Math.ceil(extent.north / dLng) : Math.floor(extent.north / dLng)) * dLng;

        // extend to make sure we cover for non refresh of tiles
        minLng = Math.max(minLng - 2 * dLng, -Math.PI);
        maxLng = Math.min(maxLng + 2 * dLng, Math.PI);
        minLat = Math.max(minLat - 2 * dLat, -Math.PI / 2);
        maxLat = Math.min(maxLat + 2 * dLng, Math.PI / 2);

        let ellipsoid = this._ellipsoid;
        let granularity = Cesium.Math.toRadians(1);

        // labels positions
        let latitudeText = minLat + Math.floor((maxLat - minLat) / dLat / 2) * dLat;
        for (let lng = minLng; lng < maxLng; lng += dLng) {
            // draw meridian
            let path = [];
            for (let lat = minLat; lat < maxLat; lat += granularity) {
                path.push(new Cesium.Cartographic(lng, lat));
            }
            path.push(new Cesium.Cartographic(lng, maxLat));
            this._polylines.add({
                positions: ellipsoid.cartographicArrayToCartesianArray(path),
                width: 0.75,
                material: new Cesium.Material({
                    fabric: {
                        type: 'Color',
                        uniforms: {
                            color: this._color
                        }
                    }
                })
            });
            let degLng = Cesium.Math.toDegrees(lng);
            this.makeLabel(lng, latitudeText, this._sexagesimal ? this._decToSex(degLng) : degLng.toFixed(gridPrecision(dLng)), false);
        }

        // lats
        let longitudeText = minLng + Math.floor((maxLng - minLng) / dLng / 2) * dLng;
        for (let lat = minLat; lat < maxLat; lat += dLat) {
            // draw parallels
            let path = [];
            for (let lng = minLng; lng < maxLng; lng += granularity) {
                path.push(new Cesium.Cartographic(lng, lat));
            }
            path.push(new Cesium.Cartographic(maxLng, lat));
            this._polylines.add({
                positions: ellipsoid.cartographicArrayToCartesianArray(path),
                width: 1,
                material: new Cesium.Material({
                    fabric: {
                        type: 'Color',
                        uniforms: {
                            color: this._color
                        }
                    }
                })
            });
            let degLat = Cesium.Math.toDegrees(lat);
            this.makeLabel(longitudeText, lat, this._sexagesimal ? this._decToSex(degLat) : degLat.toFixed(gridPrecision(dLat)), true);
        }
    };

    _.prototype.requestImage = function() {
        if (this._show) {
            this._drawGrid(this._getExtentView());
        }

        return this._canvas;
    };

    _.prototype.setVisible = function(visible) {
        this._show = visible;
        if (!visible) {
            this._polylines.removeAll();
            this._labels.removeAll();
        } else {
            this._currentExtent = null;
            this._drawGrid(this._getExtentView());
        }
    };

    _.prototype.isVisible = function() {
        return this._show;
    };

    _.prototype._decToSex = function(d) {
        var degs = Math.floor(d);
        let minimums = ((Math.abs(d) - degs) * 60.0).toFixed(2);
        if (minimums === "60.00") { degs += 1.0; mins = "0.00"; }
        return [degs, ":", minimums].join('');
    };

    _.prototype._getExtentView = function() {
        var camera = this._scene.camera;
        var canvas = this._scene.canvas;
        var corners = [
            camera.pickEllipsoid(new Cesium.Cartesian2(0, 0), this._ellipsoid),
            camera.pickEllipsoid(new Cesium.Cartesian2(canvas.width, 0), this._ellipsoid),
            camera.pickEllipsoid(new Cesium.Cartesian2(0, canvas.height), this._ellipsoid),
            camera.pickEllipsoid(new Cesium.Cartesian2(canvas.width, canvas.height), this._ellipsoid)
        ];
        for (let index = 0; index < 4; index++) {
            if (corners[index] === undefined) {
                return Cesium.Rectangle.MAX_VALUE;
            }
        }
        return Cesium.Rectangle.fromCartographicArray(this._ellipsoid.cartesianArrayToCartographicArray(corners));
    };

    _.prototype.destroy = function() {
        this._show = false;
        if (this._polylines) {
            this._scene.primitives.remove(this._polylines);
        }
        if (this._labels) {
            this._scene.primitives.remove(this._labels);
        }
    };

    function gridPrecision(dDeg) {
        if (dDeg < 0.01) return 3;
        if (dDeg < 0.1) return 2;
        if (dDeg < 1) return 1;
        return 0;
    }

    return _;

})();

Layers.registerType('graticule', {
    create: (options, map) => {
        var scene = map.scene;

        let grid = new Graticule(assign({
            tileWidth: 512,
            tileHeight: 512,
            numLines: 10
        }, options || {}), scene);

        if (options.visibility) {
            grid.setVisible(true);
        }
        return grid;
    }
});
