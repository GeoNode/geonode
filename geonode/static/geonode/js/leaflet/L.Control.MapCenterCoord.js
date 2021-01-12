L.Control.MapCenterCoord = L.Control.extend({
  // Defaults
  options: {
    position: 'bottomleft',
    icon: true,
    onMove: false,
    template: '{y} | {x}', // https://en.wikipedia.org/wiki/ISO_6709
    projected: false,
    formatProjected: '#.##0,000',
    latlngFormat: 'DD', // DD, DM, DMS
    latlngDesignators: false,
    latLngFormatter: undefined
  },

  onAdd: function (map) {
    if (this.options.icon) {
      // create a DOM element and put it into overlayPane
      this._iconEl = L.DomUtil.create('div', 'leaflet-control-mapcentercoord-icon leaflet-zoom-hide');
      map.getPanes().overlayPane.appendChild(this._iconEl);

      // add a viewreset event listener for updating icon's position
      map.on('viewreset', this._onReset, this);
      this._onReset();
    }

    // Control container
    this._container = L.DomUtil.create('div', 'leaflet-control-mapcentercoord');
    L.DomEvent.disableClickPropagation(this._container);

    // Add events listeners for updating coordinates & icon's position
    map.on('move', this._onMapMove, this);
    map.on('moveend', this._onMapMoveEnd, this);

    this._container.innerHTML = this._getMapCenterCoord();
    return this._container;
  },

  onRemove: function (map) {
    // remove icon's DOM elements and listeners
    if (this.options.icon) {
      map.getPanes().overlayPane.removeChild(this._iconEl);
      map.off('viewreset', this._onReset, this);
    }
    map.off('move', this._onMapMove, this);
    map.off('moveend', this._onMapMove, this);
  },

  _onReset: function (e) {
    // update icon's position
    var pos = this._map.latLngToLayerPoint(this._map.getCenter());
    L.DomUtil.setPosition(this._iconEl, pos);
  },

  _onMapMove: function (e) {
    if (this.options.icon) {
      // update icon's position
      var pos = this._map.latLngToLayerPoint(this._map.getCenter());
      L.DomUtil.setPosition(this._iconEl, pos);
    }
    if (this.options.onMove) {
      // update coordinates
      this._container.innerHTML = this._getMapCenterCoord();
    }
  },

  _onMapMoveEnd: function (e) {
    if (this.options.icon) {
      // update icon's position
      var pos = this._map.latLngToLayerPoint(this._map.getCenter());
      L.DomUtil.setPosition(this._iconEl, pos);
    }
    // update coordinates
    this._container.innerHTML = this._getMapCenterCoord();
  },

  _getMapCenterCoord: function () {
    if (this.options.projected) return this._getProjectedCoord(this._map.options.crs.project(this._map.getCenter()));
    return this._getLatLngCoord(this._map.getCenter());
  },

  _getProjectedCoord: function (center) {
    return L.Util.template(this.options.template, {
      x: this._format(this.options.formatProjected, center.x),
      y: this._format(this.options.formatProjected, center.y)
    });
  },


  _getLatLngCoord: function (center) {

    if (this.options.latLngFormatter != undefined) return this.options.latLngFormatter(center.lat, center.lng);

    var lat, lng, deg, min;

	//make a copy of center so we aren't affecting leaflet's internal state
    var centerCopy = {
		lat: center.lat,
		lng: center.lng
	};

    // 180 degrees & negative
    if (centerCopy.lng < 0) {
      centerCopy.lng_neg = true;
      centerCopy.lng = Math.abs(centerCopy.lng);
    } else centerCopy.lng_neg = false;
    if (centerCopy.lat < 0) {
      centerCopy.lat_neg = true;
      centerCopy.lat = Math.abs(centerCopy.lat);
    } else centerCopy.lat_neg = false;
    if (centerCopy.lng > 180) {
      centerCopy.lng = 360 - centerCopy.lng;
      centerCopy.lng_neg = !centerCopy.lng_neg;
    }

    // format
    if (this.options.latlngFormat === 'DM') {
      deg = parseInt(centerCopy.lng);
      lng = deg + 'º ' + this._format('00.000', (centerCopy.lng - deg) * 60) + "'";
      deg = parseInt(centerCopy.lat);
      lat = deg + 'º ' + this._format('00.000', (centerCopy.lat - deg) * 60) + "'";
    } else if (this.options.latlngFormat === 'DMS') {
      deg = parseInt(centerCopy.lng);
      min = (centerCopy.lng - deg) * 60;
      lng = deg + 'º ' + this._format('00', parseInt(min)) + "' " + this._format('00.0', (min - parseInt(min)) * 60) + "''";
      deg = parseInt(centerCopy.lat);
      min = (centerCopy.lat - deg) * 60;
      lat = deg + 'º ' + this._format('00', parseInt(min)) + "' " + this._format('00.0', (min - parseInt(min)) * 60) + "''";
    } else { // 'DD'
      lng = this._format('#0.00000', centerCopy.lng) + 'º';
      lat = this._format('##0.00000', centerCopy.lat) + 'º';
    }

    return L.Util.template(this.options.template, {
      x: (!this.options.latlngDesignators && centerCopy.lng_neg ? '-' : '') + lng + (this.options.latlngDesignators ? (centerCopy.lng_neg ? ' W' : ' E') : ''),
      y: (!this.options.latlngDesignators && centerCopy.lat_neg ? '-' : '') + lat + (this.options.latlngDesignators ? (centerCopy.lat_neg ? ' S' : ' N') : '')
    });
  },

  /*
   IntegraXor Web SCADA - JavaScript Number Formatter
   https://code.google.com/p/javascript-number-formatter/
   author: KPL, KHL
  */
  _format: function (m, v) {
    if (!m || isNaN(+v)) {
      return v; //return as it is.
    }
    //convert any string to number according to formation sign.
    var v = m.charAt(0) == '-' ? -v : +v;
    var isNegative = v < 0 ? v = -v : 0; //process only abs(), and turn on flag.

    //search for separator for grp & decimal, anything not digit, not +/- sign, not #.
    var result = m.match(/[^\d\-\+#]/g);
    var Decimal = (result && result[result.length - 1]) || '.'; //treat the right most symbol as decimal
    var Group = (result && result[1] && result[0]) || ','; //treat the left most symbol as group separator

    //split the decimal for the format string if any.
    var m = m.split(Decimal);
    //Fix the decimal first, toFixed will auto fill trailing zero.
    v = v.toFixed(m[1] && m[1].length);
    v = +(v) + ''; //convert number to string to trim off *all* trailing decimal zero(es)

    //fill back any trailing zero according to format
    var pos_trail_zero = m[1] && m[1].lastIndexOf('0'); //look for last zero in format
    var part = v.split('.');
    //integer will get !part[1]
    if (!part[1] || part[1] && part[1].length <= pos_trail_zero) {
      v = (+v).toFixed(pos_trail_zero + 1);
    }
    var szSep = m[0].split(Group); //look for separator
    m[0] = szSep.join(''); //join back without separator for counting the pos of any leading 0.

    var pos_lead_zero = m[0] && m[0].indexOf('0');
    if (pos_lead_zero > -1) {
      while (part[0].length < (m[0].length - pos_lead_zero)) {
        part[0] = '0' + part[0];
      }
    } else if (+part[0] == 0) {
      part[0] = '';
    }

    v = v.split('.');
    v[0] = part[0];

    //process the first group separator from decimal (.) only, the rest ignore.
    //get the length of the last slice of split result.
    var pos_separator = (szSep[1] && szSep[szSep.length - 1].length);
    if (pos_separator) {
      var integer = v[0];
      var str = '';
      var offset = integer.length % pos_separator;
      for (var i = 0, l = integer.length; i < l; i++) {

        str += integer.charAt(i); //ie6 only support charAt for sz.
        //-pos_separator so that won't trail separator on full length
        if (!((i - offset + 1) % pos_separator) && i < l - pos_separator) {
          str += Group;
        }
      }
      v[0] = str;
    }

    v[1] = (m[1] && v[1]) ? Decimal + v[1] : "";
    return (isNegative ? '-' : '') + v[0] + v[1]; //put back any negation and combine integer and fraction.
  }

});

L.Map.mergeOptions({
  MapCenterCoordControl: false
});

L.Map.addInitHook(function () {
  if (this.options.MapCenterCoordControl) {
    this.MapCenterCoordControl = new L.Control.MapCenterCoord();
    this.addControl(this.MapCenterCoordControl);
  }
});

L.control.mapCenterCoord = function (options) {
  return new L.Control.MapCenterCoord(options);
};
