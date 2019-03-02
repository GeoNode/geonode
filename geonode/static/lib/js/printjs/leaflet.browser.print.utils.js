/**
	MIT License http://www.opensource.org/licenses/mit-license.php
	Author Igor Vladyka <igor.vladyka@gmail.com> (https://github.com/Igor-Vladyka/leaflet.browser.print)
**/

L.Control.BrowserPrint.Utils = {

	_ignoreArray: [],

	_cloneFactoryArray: [],
	_cloneRendererArray: [],
	_knownRenderers: {},

	cloneOptions: function(options) {
		var utils = this;
	    var retOptions = {};
	    for (var name in options) {
	        var item = options[name];
			if (item && item.clone) {
				retOptions[name] = item.clone();
			} else if (item && item.onAdd) {
				retOptions[name] = utils.cloneLayer(item);
			} else {
				retOptions[name] = item;
			}
	    }
	    return retOptions;
	},

	cloneBasicOptionsWithoutLayers: function(options) {
	    var retOptions = {};
		var optionNames = Object.getOwnPropertyNames(options);
		if (optionNames.length) {
			for (var i = 0; i < optionNames.length; i++) {
				var optName = optionNames[i];
				if (optName && optName != "layers") {
			        retOptions[optName] = options[optName];
				}
			}

		    return this.cloneOptions(retOptions);
		}

		return retOptions;
	},

	cloneInnerLayers: function (layer) {
		var utils = this;
		var layers = [];

		layer.eachLayer(function (inner) {
			var l = utils.cloneLayer(inner);

			if (l) {
				layers.push(l);
			}
		});

		return layers;
	},

	initialize: function () {
		// Renderers
		this.registerRenderer(L.SVG, 'L.SVG');
		this.registerRenderer(L.Canvas, 'L.Canvas');

		this.registerLayer(L.MarkerClusterGroup, 'L.MarkerClusterGroup', function (layer, utils) {
			var cluster = L.markerClusterGroup(layer.options);
			cluster.addLayers(utils.cloneInnerLayers(layer));
			return cluster;
		});
		this.registerLayer(L.TileLayer.WMS, 'L.TileLayer.WMS', function(layer, utils) { 	return L.tileLayer.wms(layer._url, utils.cloneOptions(layer.options)); });
		this.registerLayer(L.TileLayer, 'L.TileLayer', function(layer, utils) { 			return L.tileLayer(layer._url, utils.cloneOptions(layer.options)); });
		this.registerLayer(L.GridLayer, 'L.GridLayer', function(layer, utils) { 			return L.gridLayer(utils.cloneOptions(layer.options)); });
		this.registerLayer(L.ImageOverlay, 'L.ImageOverlay', function(layer, utils) { 		return L.imageOverlay(layer._url, layer._bounds, utils.cloneOptions(layer.options)); });
		this.registerLayer(L.Marker, 'L.Marker', function(layer, utils) { 					return L.marker(layer.getLatLng(), utils.cloneOptions(layer.options)); });
		this.registerLayer(L.Popup, 'L.Popup', function(layer, utils) { 					return L.popup(utils.cloneOptions(layer.options)).setLatLng(layer.getLatLng()).setContent(layer.getContent()); });
		this.registerLayer(L.Circle, 'L.Circle', function(layer, utils) { 					return L.circle(layer.getLatLng(), layer.getRadius(), utils.cloneOptions(layer.options)); });
		this.registerLayer(L.CircleMarker, 'L.CircleMarker', function(layer, utils) { 		return L.circleMarker(layer.getLatLng(), utils.cloneOptions(layer.options)); });
		this.registerLayer(L.Rectangle, 'L.Rectangle', function(layer, utils) { 			return L.rectangle(layer.getBounds(), utils.cloneOptions(layer.options)); });
		this.registerLayer(L.Polygon, 'L.Polygon', function(layer, utils) { 				return L.polygon(layer.getLatLngs(), utils.cloneOptions(layer.options)); });

		// MultiPolyline is removed in leaflet 1.0.0
		this.registerLayer(L.MultiPolyline, 'L.MultiPolyline', function(layer, utils) { 	return L.polyline(layer.getLatLngs(), utils.cloneOptions(layer.options)); });
		// MultiPolygon is removed in leaflet 1.0.0
		this.registerLayer(L.MultiPolygon, 'L.MultiPolygon', function(layer, utils) { 		return L.multiPolygon(layer.getLatLngs(), utils.cloneOptions(layer.options)); });

		this.registerLayer(L.Polyline, 'L.Polyline', function(layer, utils) { 				return L.polyline(layer.getLatLngs(), utils.cloneOptions(layer.options)); });
		this.registerLayer(L.GeoJSON, 'L.GeoJSON', function(layer, utils) { 				return L.geoJson(layer.toGeoJSON(), utils.cloneOptions(layer.options)); });

		this.registerIgnoreLayer(L.FeatureGroup, 'L.FeatureGroup');
		this.registerIgnoreLayer(L.LayerGroup, 'L.LayerGroup');

		// There is no point to clone tooltips here;  L.tooltip(options);
		this.registerLayer(L.Tooltip, 'L.Tooltip', function(){	return null; });
	},

	_register: function(array, type, identifier, builderFunction) {
		if (type &&
			!array.filter(function(l){ return l.identifier === identifier; }).length) {

			array.push({
				type: type,
				identifier: identifier,
				builder: builderFunction || function (layer) { return new type(layer.options); }
			});
		}
	},

	registerLayer: function(type, identifier, builderFunction) {
		this._register(this._cloneFactoryArray, type, identifier, builderFunction);
	},

	registerRenderer: function(type, identifier, builderFunction) {
		this._register(this._cloneRendererArray, type, identifier, builderFunction);
	},

	registerIgnoreLayer: function(type, identifier) {
		this._register(this._ignoreArray, type, identifier);
	},

	cloneLayer: function(layer) {
		if (!layer) return null;

		// First we check if this layer is actual renderer
		var renderer = this.__getRenderer(layer);
		if (renderer) {
			return renderer;
		}

		// We clone and recreate layer if it's simple overlay
		var factoryObject = this.__getFactoryObject(layer);
		if (factoryObject) {
			factoryObject = factoryObject.builder(layer, this);
		}

		return factoryObject;
	},

	getType: function(layer) {
		if (!layer) return null;

		var factoryObject = this.__getFactoryObject(layer);
		if (factoryObject) {
			factoryObject = factoryObject.identifier;
		}

		return factoryObject;
	},

	__getRenderer: function(oldRenderer) {
		var renderer = this._knownRenderers[oldRenderer._leaflet_id];
		if (!renderer) {
			for (var i = 0; i < this._cloneRendererArray.length; i++) {
				var factoryObject = this._cloneRendererArray[i];
				if (oldRenderer instanceof factoryObject.type) {
					this._knownRenderers[oldRenderer._leaflet_id] = factoryObject.builder(oldRenderer.options);
					break;
				}
			}

			renderer = this._knownRenderers[oldRenderer._leaflet_id];
		}

		return renderer;
	},

	__getFactoryObject: function (layer) {
		this.initialize();

		for (var i = 0; i < this._ignoreArray.length; i++) {
			var ignoreObject = this._ignoreArray[i];
			if (ignoreObject.type && layer instanceof ignoreObject.type) {
				return null;
			}
		}

		for (var i = 0; i < this._cloneFactoryArray.length; i++) {
			var factoryObject = this._cloneFactoryArray[i];
			if (factoryObject.type && layer instanceof factoryObject.type) {
				return factoryObject;
			}
		}

		this.__unknownLayer__();

		return null;
	},

	__unknownLayer__: function(){
	   console.warn('Unknown layer, cannot clone this layer. Leaflet-version: ' + L.version);
	   console.info('Please use "L.Control.BrowserPrint.Utils.registerLayer(/*layerFunction*/, "layerIdentifierString", constructorFunction)" to register new layers.');
	   console.info('WMS Layer registration Example: L.Control.BrowserPrint.Utils.registerLayer(L.TileLayer.WMS, "L.TileLayer.WMS", function(layer, utils) { return L.tileLayer.wms(layer._url, layer.options); });');
	   console.info('For additional information please refer to documentation on: https://github.com/Igor-Vladyka/leaflet.browser.print.');
	   console.info('-------------------------------------------------------------------------------------------------------------------');
   }
};
