// Following https://github.com/Leaflet/Leaflet/blob/master/PLUGIN-GUIDE.md
(function (factory, window) {

	// define an AMD module that relies on 'leaflet'
	if (typeof define === 'function' && define.amd) {
		define(['leaflet'], factory);

	// define a Common JS module that relies on 'leaflet'
	} else if (typeof exports === 'object') {
		module.exports = factory(require('leaflet'));
	}

	// attach your plugin to the global 'L' variable
	if (typeof window !== 'undefined' && window.L) {
		window.L.Control.NavBar = factory(L);
		window.L.control.navbar = function (layer, options) {
			return new window.L.Control.NavBar(layer, options);
		};
	}
}(function (L) {

	var NavBar = L.Control.extend({
    options: {
      //position: 'topleft',
      //center:,
      //zoom :,
      forwardTitle: 'Go forward in map view history',
      backTitle: 'Go back in map view history',
      homeTitle: 'Go to home map view'
    },

    onAdd: function(map) {

      // Set options
      if (!this.options.center) {
        this.options.center = map.getCenter();
      }
      if (!this.options.zoom) {
        this.options.zoom = map.getZoom();
      }
      options = this.options;

      // Create toolbar
      var controlName = 'leaflet-control-navbar',
      container = L.DomUtil.create('div', controlName + ' leaflet-bar');

      // Add toolbar buttons
      this._homeButton = this._createButton(options.homeTitle, controlName + '-home', container, this._goHome);
      this._fwdButton = this._createButton(options.forwardTitle, controlName + '-fwd', container, this._goFwd);
      this._backButton = this._createButton(options.backTitle, controlName + '-back', container, this._goBack);

      // Initialize view history and index
      this._viewHistory = [{center: this.options.center, zoom: this.options.zoom}];
      this._curIndx = 0;
      this._updateDisabled();
      map.once('moveend', function() {this._map.on('moveend', this._updateHistory, this);}, this);
      // Set intial view to home
      map.setView(options.center, options.zoom);

      return container;
    },

    onRemove: function(map) {
      map.off('moveend', this._updateHistory, this);
    },

    _goHome: function() {
      this._map.setView(this.options.center, this.options.zoom);
    },

    _goBack: function() {
      if (this._curIndx !== 0) {
        this._map.off('moveend', this._updateHistory, this);
        this._map.once('moveend', function() {this._map.on('moveend', this._updateHistory, this);}, this);
        this._curIndx--;
        this._updateDisabled();
        var view = this._viewHistory[this._curIndx];
        this._map.setView(view.center, view.zoom);
      }
    },

    _goFwd: function() {
      if (this._curIndx != this._viewHistory.length - 1) {
        this._map.off('moveend', this._updateHistory, this);
        this._map.once('moveend', function() {this._map.on('moveend', this._updateHistory, this);}, this);
        this._curIndx++;
        this._updateDisabled();
        var view = this._viewHistory[this._curIndx];
        this._map.setView(view.center, view.zoom);
      }
    },

    _createButton: function(title, className, container, fn) {
      // Modified from Leaflet zoom control

      var link = L.DomUtil.create('a', className, container);
      link.href = '#';
      link.title = title;

      L.DomEvent
      .on(link, 'mousedown dblclick', L.DomEvent.stopPropagation)
      .on(link, 'click', L.DomEvent.stop)
      .on(link, 'click', fn, this)
      .on(link, 'click', this._refocusOnMap, this);

      return link;
    },

    _updateHistory: function() {
      var newView = {center: this._map.getCenter(), zoom: this._map.getZoom()};
      var insertIndx = this._curIndx + 1;
      this._viewHistory.splice(insertIndx, this._viewHistory.length - insertIndx, newView);
      this._curIndx++;
      // Update disabled state of toolbar buttons
      this._updateDisabled();
    },

    _setFwdEnabled: function(enabled) {
      var leafletDisabled = 'leaflet-disabled';
      var fwdDisabled = 'leaflet-control-navbar-fwd-disabled';
      if (enabled === true) {
        L.DomUtil.removeClass(this._fwdButton, fwdDisabled);
        L.DomUtil.removeClass(this._fwdButton, leafletDisabled);
      }else {
        L.DomUtil.addClass(this._fwdButton, fwdDisabled);
        L.DomUtil.addClass(this._fwdButton, leafletDisabled);
      }
    },

    _setBackEnabled: function(enabled) {
      var leafletDisabled = 'leaflet-disabled';
      var backDisabled = 'leaflet-control-navbar-back-disabled';
      if (enabled === true) {
        L.DomUtil.removeClass(this._backButton, backDisabled);
        L.DomUtil.removeClass(this._backButton, leafletDisabled);
      }else {
        L.DomUtil.addClass(this._backButton, backDisabled);
        L.DomUtil.addClass(this._backButton, leafletDisabled);
      }
    },

    _updateDisabled: function() {
      if (this._curIndx == (this._viewHistory.length - 1)) {
        this._setFwdEnabled(false);
      }else {
        this._setFwdEnabled(true);
      }

      if (this._curIndx <= 0) {
        this._setBackEnabled(false);
      }else {
        this._setBackEnabled(true);
      }
    }

  });

	L.Map.mergeOptions({
		navBarControl: false
	});

	L.Map.addInitHook(function () {
		if (this.options.navBarControl) {
			this.navBarControl = (new NavBar()).addTo(this);
		}
	});

	return NavBar;

}, window));
