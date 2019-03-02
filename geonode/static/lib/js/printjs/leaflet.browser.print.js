/**
	MIT License http://www.opensource.org/licenses/mit-license.php
	Author Igor Vladyka <igor.vladyka@gmail.com> (https://github.com/Igor-Vladyka/leaflet.browser.print)
**/

L.Control.BrowserPrint = L.Control.extend({
	options: {
		title: 'Print map',
		documentTitle: '',
		position: 'topleft',
        printLayer: null,
		printModes: ["Portrait", "Landscape", "Auto", "Custom"],
		closePopupsOnPrint: true,
		contentSelector: "[leaflet-browser-print-content]",
		pagesSelector: "[leaflet-browser-print-pages]",
		manualMode: false
	},

	onAdd: function (map) {

		var container = L.DomUtil.create('div', 'leaflet-control-browser-print leaflet-bar leaflet-control');
		L.DomEvent.disableClickPropagation(container);

		this._appendControlStyles(container);

		if (this.options.printModes.length > 1) {
			L.DomEvent.addListener(container, 'mouseover', this._displayPageSizeButtons, this);
			L.DomEvent.addListener(container, 'mouseout', this._hidePageSizeButtons, this);
		} else {
			container.style.cursor = "pointer";
		}

		if (this.options.position.indexOf("left") > 0) {
			this._createIcon(container);
			this._createMenu(container);
		} else {
			this._createMenu(container);
			this._createIcon(container);
		}

		setTimeout( function () {
			container.className += parseInt(L.version) ? " v1" : " v0-7"; // parseInt(L.version) returns 1 for v1.0.3 and 0 for 0.7.7;
		}, 10);

		map.printControl = this; // Make control available from the map object itself;
		return container;
	},

	_createIcon: function (container) {
		this.__link__ = L.DomUtil.create('a', '', container);
		this.__link__.className = "leaflet-browser-print";
		if (this.options.title) {
			this.__link__.title = this.options.title;
		}
		return this.__link__;
	},

	_createMenu: function (container) {
		var domPrintModes = [];

		for (var i = 0; i < this.options.printModes.length; i++) {
			var mode = this.options.printModes[i];

			/*
				Mode:
					Mode: Portrait/Landscape/Auto/Custom
					Title: 'Portrait'/'Landscape'/'Auto'/'Custom'
					PageSize: 'A3'/'A4'
					Action: '_printPortrait'/...
					InvalidateBounds: true/false
			*/
			if (mode.length) {
				var key = mode[0].toUpperCase() + mode.substring(1).toLowerCase();

				mode = L.control.browserPrint.mode[mode.toLowerCase()](this._getDefaultTitle(key));

			} else if (mode instanceof L.Control.BrowserPrint.Mode) {
				// Looks like everythin is fine.
			} else {
				throw "Invalid Print Mode. Can't construct logic to print current map."
			}

			if (this.options.printModes.length == 1) {
				mode.Element = container;
			} else {
				mode.Element = L.DomUtil.create('li', 'browser-print-mode', L.DomUtil.create('ul', 'browser-print-holder', container));
				mode.Element.innerHTML = mode.Title;
			}

			L.DomEvent.addListener(mode.Element, 'click', mode.Action(this, mode), this);

			domPrintModes.push(mode);
		}

		this.options.printModes = domPrintModes;
	},

	_getDefaultTitle: function(key) {
		return this.options.printModesNames && this.options.printModesNames[key] || key;
	},

    _displayPageSizeButtons: function() {
		if (this.options.position.indexOf("left") > 0) {
	        this.__link__.style.borderTopRightRadius = "0px";
	    	this.__link__.style.borderBottomRightRadius = "0px";
		} else {
			this.__link__.style.borderTopLeftRadius = "0px";
	    	this.__link__.style.borderBottomLeftRadius = "0px";
		}

		this.options.printModes.forEach(function(mode){
			mode.Element.style.display = "inline-block";
		});
    },

    _hidePageSizeButtons: function (){
		if (this.options.position.indexOf("left") > 0) {
	    	this.__link__.style.borderTopRightRadius = "";
	    	this.__link__.style.borderBottomRightRadius = "";
		} else {
	    	this.__link__.style.borderTopLeftRadius = "";
	    	this.__link__.style.borderBottomLeftRadius = "";
		}

		this.options.printModes.forEach(function(mode){
			mode.Element.style.display = "";
		});
    },

	_getMode: function(name, invalidateBounds) {
		var mode = this.options.printModes.filter(function(f){
			return f.Mode == name;
		})[0];

		return new L.control.browserPrint.mode(mode.Mode, mode.Title, mode.PageSize, mode.Action, invalidateBounds || mode.InvalidateBounds);
	},

    _printLandscape: function () {
		this._addPrintClassToContainer(this._map, "leaflet-browser-print--landscape");
		var orientation = "Landscape";
        this._print(this._getMode(orientation), orientation);
    },

    _printPortrait: function () {
		this._addPrintClassToContainer(this._map, "leaflet-browser-print--portrait");
		var orientation = "Portrait";
        this._print(this._getMode(orientation), orientation);
    },

    _printAuto: function () {
		this._addPrintClassToContainer(this._map, "leaflet-browser-print--auto");

		var autoBounds = this._getBoundsForAllVisualLayers();
		var orientation = this._getPageSizeFromBounds(autoBounds);
		this._print(this._getMode(orientation, true), orientation, autoBounds);
    },

    _printCustom: function () {
		this._addPrintClassToContainer(this._map, "leaflet-browser-print--custom");
		this._map.on('mousedown', this._startAutoPoligon, this);
    },

	_addPrintClassToContainer: function (map, printClassName) {
		var container = map.getContainer();

		if (container.className.indexOf(printClassName) === -1) {
			container.className += " " + printClassName;
		}
	},

	_removePrintClassFromContainer: function (map, printClassName) {
		var container = map.getContainer();

		if (container.className && container.className.indexOf(printClassName) > -1) {
			container.className = container.className.replace(" " + printClassName, "");
		}
	},

	_startAutoPoligon: function (e) {
		e.originalEvent.preventDefault();
		e.originalEvent.stopPropagation();

		this._map.dragging.disable();

		this.options.custom = { start: e.latlng };

		this._map.off('mousedown', this._startAutoPoligon, this);
		this._map.on('mousemove', this._moveAutoPoligon, this);
		this._map.on('mouseup', this._endAutoPoligon, this);
	},

	_moveAutoPoligon: function (e) {
		if (this.options.custom) {
			e.originalEvent.preventDefault();
			e.originalEvent.stopPropagation();
			if (this.options.custom.rectangle) {
				this.options.custom.rectangle.setBounds(L.latLngBounds(this.options.custom.start, e.latlng));
			} else {
				this.options.custom.rectangle = L.rectangle([this.options.custom.start, e.latlng], { color: "gray", dashArray: '5, 10' });
				this.options.custom.rectangle.addTo(this._map);
			}
		}
	},

	_endAutoPoligon: function (e) {

		e.originalEvent.preventDefault();
		e.originalEvent.stopPropagation();

		this._map.off('mousemove', this._moveAutoPoligon, this);
		this._map.off('mouseup', this._endAutoPoligon, this);

		this._map.dragging.enable();

		if (this.options.custom && this.options.custom.rectangle) {
			var autoBounds = this.options.custom.rectangle.getBounds();

			this._map.removeLayer(this.options.custom.rectangle);
			this.options.custom = undefined;

			var orientation = this._getPageSizeFromBounds(autoBounds);
			this._print(this._getMode(orientation, true), orientation, autoBounds);
		} else {
			this._clearPrint();
		}
	},

	_getPageSizeFromBounds: function(bounds) {
		var height = Math.abs(bounds.getNorth() - bounds.getSouth());
		var width = Math.abs(bounds.getEast() - bounds.getWest());
		if (height > width) {
			return "Portrait";
		} else {
			return "Landscape";
		}
	},

	_setupPrintPagesWidth: function(pagesContainer, size, pageOrientation) {
		pagesContainer.style.width = pageOrientation === "Landscape" ? size.Height : size.Width;
	},

	_setupPrintMapHeight: function(mapContainer, size, pageOrientation) {
		mapContainer.style.height = pageOrientation === "Landscape" ? size.Width : size.Height;
	},

	/* Intended to cancel next printing*/
	cancel: function(cancelNextPrinting){
		this.cancelNextPrinting = cancelNextPrinting;
	},

	print: function(pageOrientation, autoBounds) {
		if (pageOrientation == "Landscape" || pageOrientation == "Portrait") {
			this._print(this._getMode(pageOrientation, !!autoBounds), pageOrientation, autoBounds);
		}
	},

    _print: function (printMode, pageOrientation, autoBounds) {
		var self = this;
        var mapContainer = this._map.getContainer();

        var origins = {
            bounds: autoBounds || this._map.getBounds(),
            width: mapContainer.style.width,
            height: mapContainer.style.height,
			documentTitle: document.title,
			printLayer: L.Control.BrowserPrint.Utils.cloneLayer(this.options.printLayer),
			panes: []
        };

		var mapPanes = this._map.getPanes();
		for (var pane in mapPanes) {
			origins.panes.push({name: pane, container: undefined});
		}

		origins.printObjects = this._getPrintObjects(origins.printLayer);

		this._map.fire(L.Control.BrowserPrint.Event.PrePrint, { printLayer: origins.printLayer, printObjects: origins.printObjects, pageOrientation: pageOrientation, printMode: printMode.Mode, pageBounds: origins.bounds});

		if (this.cancelNextPrinting) {
			delete this.cancelNextPrinting;
			return;
		}

		var overlay = this._addPrintMapOverlay(printMode.PageSize, printMode.getPageMargin(), printMode.getSize(), pageOrientation, origins);

		if (this.options.documentTitle) {
			document.title = this.options.documentTitle;
		}

		this._map.fire(L.Control.BrowserPrint.Event.PrintStart, { printLayer: origins.printLayer, printMap: overlay.map, printObjects: overlay.objects });

		if (printMode.InvalidateBounds) {
			overlay.map.fitBounds(origins.bounds);
			overlay.map.invalidateSize({reset: true, animate: false, pan: false});
		} else {
			overlay.map.setView(this._map.getCenter(), this._map.getZoom());
		}

		var interval = setInterval(function(){
			if (!self._isTilesLoading(overlay.map)) {
				clearInterval(interval);
				if (self.options.manualMode) {
					self._setupManualPrintButton(overlay.map, origins, overlay.objects);
				} else {
					self._completePrinting(overlay.map, origins, overlay.objects);
				}
			}
		}, 50);
    },

	_completePrinting: function (overlayMap, origins, printObjects) {
		var self = this;
		setTimeout(function(){
			self._map.fire(L.Control.BrowserPrint.Event.Print, { printLayer: origins.printLayer, printMap: overlayMap, printObjects: printObjects });
			var printPromise = window.print();
			if (printPromise) {
				Promise.all([printPromise]).then(function(){
					self._printEnd(origins);
					self._map.fire(L.Control.BrowserPrint.Event.PrintEnd, { printLayer: origins.printLayer, printMap: overlayMap, printObjects: printObjects });
				})
			} else {
				self._printEnd(origins);
				self._map.fire(L.Control.BrowserPrint.Event.PrintEnd, { printLayer: origins.printLayer, printMap: overlayMap, printObjects: printObjects });
			}
		}, 1000);
	},

    _getBoundsForAllVisualLayers: function () {
	    var fitBounds = null;

        // Getting all layers without URL -> not tiles.
        for (var layerId in this._map._layers){
            var layer = this._map._layers[layerId];
            if (!layer._url && !layer._mutant) {
                if (fitBounds) {
                    if (layer.getBounds) {
                        fitBounds.extend(layer.getBounds());
                    } else if(layer.getLatLng){
                        fitBounds.extend(layer.getLatLng());
                    }
                } else {
                    if (layer.getBounds) {
                        fitBounds = layer.getBounds();
                    } else if(layer.getLatLng){
                        fitBounds = L.latLngBounds(layer.getLatLng(), layer.getLatLng());
                    }
                }
            }
        }

		if (!fitBounds) {
			fitBounds = this._map.getBounds();
		}

		return fitBounds;
    },

	_clearPrint: function () {
		this._removePrintClassFromContainer(this._map, "leaflet-browser-print--landscape");
		this._removePrintClassFromContainer(this._map, "leaflet-browser-print--portrait");
		this._removePrintClassFromContainer(this._map, "leaflet-browser-print--auto");
		this._removePrintClassFromContainer(this._map, "leaflet-browser-print--custom");
	},

    _printEnd: function (origins) {
		this._clearPrint();

		document.body.removeChild(this.__overlay__);
		this.__overlay__ = null;

		document.body.className = document.body.className.replace(" leaflet--printing", "");
		if (this.options.documentTitle) {
			document.title = origins.documentTitle;
		}

		this._map.invalidateSize({reset: true, animate: false, pan: false});
    },

    /*_validatePrintLayer: function() {
		var visualLayerForPrinting = null;

        if (this.options.printLayer) {
			visualLayerForPrinting = this.options.printLayer;
        } else {
            for (var id in this._map._layers){
                var pLayer = this._map._layers[id];
                if (pLayer._url) {
                    visualLayerForPrinting = pLayer;
					break;
                }
            }
		}

		return visualLayerForPrinting;
    },*/

	_getPrintObjects: function(printLayer) {
		var printObjects = {};
		for (var id in this._map._layers){
			var layer = this._map._layers[id];
			if (!printLayer || !layer._url || layer instanceof L.TileLayer.WMS) {
				var type = L.Control.BrowserPrint.Utils.getType(layer);
				if (type) {
					if (!printObjects[type]) {
						printObjects[type] = [];
					}
					printObjects[type].push(layer);
				}
			}
		}

		return printObjects;
	},

    _addPrintCss: function (pageSize, pageMargin, pageOrientation) {

        var printStyleSheet = document.createElement('style');
		printStyleSheet.className = "leaflet-browser-print-css";
        printStyleSheet.setAttribute('type', 'text/css');
		printStyleSheet.innerHTML = ' @media print { .leaflet-popup-content-wrapper, .leaflet-popup-tip { box-shadow: none; }';
		printStyleSheet.innerHTML += ' .leaflet-browser-print--manualMode-button { display: none; }';
		printStyleSheet.innerHTML += ' * { -webkit-print-color-adjust: exact!important; printer-colors: exact!important; color-adjust: exact!important; }';
		if (pageMargin) {
			printStyleSheet.innerHTML += ' @page { margin: ' + pageMargin + '; }';
		}
		printStyleSheet.innerHTML += ' @page :first { page-break-after: always; }';

        switch (pageOrientation) {
            case "Landscape":
                printStyleSheet.innerText += " @page { size : " + pageSize + " landscape; }";
                break;
            default:
            case "Portrait":
                printStyleSheet.innerText += " @page { size : " + pageSize + " portrait; }";
                break;
        }

        return printStyleSheet;
    },

	_appendControlStyles:  function (container) {
		var printControlStyleSheet = document.createElement('style');
		printControlStyleSheet.setAttribute('type', 'text/css');

		printControlStyleSheet.innerHTML += " .leaflet-control-browser-print { display: flex; } .leaflet-control-browser-print a { background: #fff url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gcCCi8Vjp+aNAAAAGhJREFUOMvFksENgDAMA68RC7BBN+Cf/ZU33QAmYAT6BolAGxB+RrrIsg1BpfNBVXcPMLMDI/ytpKozMHWwK7BJJ7yYWQbGdBea9wTIkRDzKy0MT7r2NiJACRgotCzxykFI34QY2Ea7KmtxGJ+uX4wfAAAAAElFTkSuQmCC') no-repeat 5px; background-size: 16px 16px; display: block; border-radius: 2px; }";

		printControlStyleSheet.innerHTML += " .v0-7.leaflet-control-browser-print a.leaflet-browser-print { width: 26px; height: 26px; } .v1.leaflet-control-browser-print a.leaflet-browser-print { background-position-x: 7px; }";
		printControlStyleSheet.innerHTML += " .browser-print-holder { margin: 0px; padding: 0px; list-style: none; white-space: nowrap; } .browser-print-holder-left li:last-child { border-top-right-radius: 2px; border-bottom-right-radius: 2px; } .browser-print-holder-right li:first-child { border-top-left-radius: 2px; border-bottom-left-radius: 2px; }";
		printControlStyleSheet.innerHTML += " .browser-print-mode { display: none; background-color: #919187; color: #FFF; font: 11px/19px 'Helvetica Neue', Arial, Helvetica, sans-serif; text-decoration: none; padding: 4px 10px; text-align: center; } .v1 .browser-print-mode { padding: 6px 10px; } .browser-print-mode:hover { background-color: #757570; cursor: pointer; }";
		printControlStyleSheet.innerHTML += " .leaflet-browser-print--custom, .leaflet-browser-print--custom path { cursor: crosshair!important; }";
		printControlStyleSheet.innerHTML += " .leaflet-print-overlay { width: 100%; height:auto; min-height: 100%; position: absolute; top: 0; background-color: white!important; left: 0; z-index: 1001; display: block!important; } ";
		printControlStyleSheet.innerHTML += " .leaflet--printing { height:auto; min-height: 100%; margin: 0px!important; padding: 0px!important; } body.leaflet--printing > * { display: none; box-sizing: border-box; }";
		printControlStyleSheet.innerHTML += " .grid-print-container { grid-template: 1fr / 1fr; box-sizing: border-box; } .grid-map-print { grid-row: 1; grid-column: 1; } body.leaflet--printing .grid-print-container [leaflet-browser-print-content]:not(style) { display: unset!important; }";
		printControlStyleSheet.innerHTML += " .pages-print-container { box-sizing: border-box; }";

        container.appendChild(printControlStyleSheet);
	},

	_setupManualPrintButton: function(map, origins, objects) {
		var manualPrintButton = document.createElement('button');
		manualPrintButton.className = "leaflet-browser-print--manualMode-button";
		manualPrintButton.innerHTML = "Print";
		manualPrintButton.style.position = "absolute";
		manualPrintButton.style.top = "20px";
		manualPrintButton.style.right = "20px";
		this.__overlay__.appendChild(manualPrintButton);

		var self = this;
		L.DomEvent.addListener(manualPrintButton, 'click', function () {
			self._completePrinting(map, origins, objects);
		});
	},

	_addPrintMapOverlay: function (pageSize, pageMargin, printSize, pageOrientation, origins) {
		this.__overlay__ = document.createElement("div");
		this.__overlay__.className = this._map.getContainer().className + " leaflet-print-overlay";
		document.body.appendChild(this.__overlay__);

		this.__overlay__.appendChild(this._addPrintCss(pageSize, pageMargin, pageOrientation));

		var gridContainer = document.createElement("div");
		gridContainer.className = "grid-print-container";
		gridContainer.style.width = "100%";
		gridContainer.style.display = "grid";
		this._setupPrintMapHeight(gridContainer, printSize, pageOrientation);

		if (this.options.contentSelector) {
			var content = document.querySelectorAll(this.options.contentSelector);
			if (content && content.length) {
				for (var i = 0; i < content.length; i++) {
					var printContentItem = content[i].cloneNode(true);
					gridContainer.appendChild(printContentItem);
				}
			}
		}

		var isMultipage = this.options.pagesSelector && document.querySelectorAll(this.options.pagesSelector).length;
		if (isMultipage) {
			var pagesContainer = document.createElement("div");
			pagesContainer.className = "pages-print-container";
			pagesContainer.style.margin = "0!important";
			this._setupPrintPagesWidth(pagesContainer, printSize, pageOrientation);

			this.__overlay__.appendChild(pagesContainer);
			pagesContainer.appendChild(gridContainer);

			var pages = document.querySelectorAll(this.options.pagesSelector);
			if (pages && pages.length) {
				for (var i = 0; i < pages.length; i++) {
					var printPageItem = pages[i].cloneNode(true);
					pagesContainer.appendChild(printPageItem);
				}
			}
		} else {
			this._setupPrintPagesWidth(gridContainer, printSize, pageOrientation);
			this.__overlay__.appendChild(gridContainer);
		}

		var overlayMapDom = document.createElement("div");
		overlayMapDom.id = this._map.getContainer().id + "-print";
		overlayMapDom.className = "grid-map-print";
		overlayMapDom.style.width = "100%";
		overlayMapDom.style.height = "100%";
		gridContainer.appendChild(overlayMapDom);

		document.body.className += " leaflet--printing";

		var newMapOptions = L.Control.BrowserPrint.Utils.cloneBasicOptionsWithoutLayers(this._map.options);
		newMapOptions.maxZoom = this._map.getMaxZoom();
		return this._setupPrintMap(overlayMapDom.id, newMapOptions, origins.printLayer, origins.printObjects, origins.panes);
	},

	_setupPrintMap: function (id, options, printLayer, printObjects, panes) {
		options.zoomControl = false;
		var overlayMap = L.map(id, options);

		if (printLayer) {
			printLayer.addTo(overlayMap);
		}

		panes.forEach(function(p) { overlayMap.createPane(p.name, p.container); });

		for (var type in printObjects){
			var closePopupsOnPrint = this.options.closePopupsOnPrint;
			printObjects[type] = printObjects[type].map(function(pLayer){
				var clone = L.Control.BrowserPrint.Utils.cloneLayer(pLayer);

				if (clone) {
					/* Workaround for apropriate handling of popups. */
					if (pLayer instanceof L.Popup){
						if(!pLayer.isOpen) {
							pLayer.isOpen = function () { return this._isOpen; };
						}
						if (pLayer.isOpen() && !closePopupsOnPrint) {
							clone.openOn(overlayMap);
						}
					} else {
						clone.addTo(overlayMap);
					}

					if (pLayer instanceof L.Layer) {
						var tooltip = pLayer.getTooltip();
						if (tooltip) {
							clone.bindTooltip(tooltip.getContent(), tooltip.options);
							if (pLayer.isTooltipOpen()) {
								clone.openTooltip(tooltip.getLatLng());
							}
						}
					}

					return clone;
				}
			});
		}

		return {map: overlayMap, objects: printObjects};
	},

	// Get all layers that is tile layers and is still loading;
	_isTilesLoading: function(overlayMap){
		var isLoading = false;
		var mapMajorVersion = parseFloat(L.version);
		if (mapMajorVersion > 1) {
			isLoading = this._getLoadingLayers(overlayMap);
		} else {
			isLoading = overlayMap._tilesToLoad || overlayMap._tileLayersToLoad;
		}

		return isLoading;
	},

	_getLoadingLayers: function(map) {
		for (var l in map._layers) {
			var layer = map._layers[l];
			if ((layer._url || layer._mutant) && layer._loading) {
				return true;
			}
		}

		return false;
	}
});

L.Control.BrowserPrint.Event =  {
	PrePrint: 'browser-pre-print',
	PrintStart: 'browser-print-start',
	Print: 'browser-print',
	PrintEnd: 'browser-print-end'
},

L.control.browserPrint = function(options) {
	if (!options || !options.printModes) {
		options = options || {};
		options.printModes = [
			L.control.browserPrint.mode.portrait(),
			L.control.browserPrint.mode.landscape(),
			L.control.browserPrint.mode.auto(),
			L.control.browserPrint.mode.custom()
		]
	}

	if (options && options.printModes && (!options.printModes.filter || !options.printModes.length)) {
		throw "Please specify valid print modes for Print action. Example: printModes: [L.control.browserPrint.mode.portrait(), L.control.browserPrint.mode.auto('Automatico'), 'Custom']";
	}

	if (options.printModesNames) {
		console.warn("'printModesNames' option is obsolete. Please use 'L.control.browserPrint.mode.*(/*Title*/)' shortcut instead. Please check latest release and documentation.");
	}

	return new L.Control.BrowserPrint(options);
};
