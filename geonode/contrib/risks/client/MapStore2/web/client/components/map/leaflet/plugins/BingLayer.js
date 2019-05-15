/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/leaflet/Layers');
var Bing = require('leaflet-plugins/layer/tile/Bing');
const assign = require('object-assign');
const L = require('leaflet');

Bing.prototype.loadMetadata = function() {
    var _this = this;
    var cbid = '_bing_metadata_' + L.Util.stamp(this);
    window[cbid] = function(meta) {
        _this.meta = meta;
        window[cbid] = undefined;
        const e = document.getElementById(cbid);
        e.parentNode.removeChild(e);
        if (meta.errorDetails) {
            _this.fire('load', {layer: _this});
            return _this.onError(meta);
        }
        _this.initMetadata();
    };
    const urlScheme = (document.location.protocol === 'file:') ? 'https' : document.location.protocol.slice(0, -1);
    const url = urlScheme + '://dev.virtualearth.net/REST/v1/Imagery/Metadata/'
                + this.options.type + '?include=ImageryProviders&jsonp=' + cbid +
                '&key=' + this._key + '&UriScheme=' + urlScheme;
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = url;
    script.id = cbid;
    document.getElementsByTagName('head')[0].appendChild(script);
};

Bing.prototype.onError = function(meta) {
    if (this.options.onError) {
        return this.options.onError(meta);
    }
};

Layers.registerType('bing', {
    create: (options) => {
        var key = options.apiKey;
        let layerOptions = {
            subdomains: [0, 1, 2, 3],
            type: options.name,
            attribution: 'Bing',
            culture: '',
            onError: options.onError
        };
        if (options.zoomOffset) {
            layerOptions = assign({}, layerOptions, {
                zoomOffset: options.zoomOffset
            });
        }
        return new Bing(key, layerOptions);
    },
    isValid: (layer) => {
        if (layer.meta && layer.meta.statusCode && layer.meta.statusCode !== 200) {
            return false;
        }
        return true;
    }
});
