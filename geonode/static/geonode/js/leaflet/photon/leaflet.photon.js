
L.Control.Photon = L.Control.extend({

    includes: L.Mixin.Events,

    options: {
        url: 'http://photon.komoot.io/api/?',
        placeholder: "Start typing...",
        emptyMessage: "No result",
        minChar: 3,
        limit: 5,
        submitDelay: 300,
        includePosition: true,
        noResultLabel: "No result",
        feedbackEmail: "photon@komoot.de" // Set to null to remove feedback box
    },

    CACHE: '',
    RESULTS: [],
    KEYS: {
        LEFT: 37,
        UP: 38,
        RIGHT: 39,
        DOWN: 40,
        TAB: 9,
        RETURN: 13,
        ESC: 27,
        APPLE: 91,
        SHIFT: 16,
        ALT: 17,
        CTRL: 18
    },

    onAdd: function (map, options) {
        this.map = map;
        this.container = L.DomUtil.create('div', 'leaflet-photon');

        this.options = L.Util.extend(this.options, options);
        var CURRENT = null;

        try {
            Object.defineProperty(this, "CURRENT", {
                get: function () {
                    return CURRENT;
                },
                set: function (index) {
                    if (typeof index === "object") {
                        index = this.resultToIndex(index);
                    }
                    CURRENT = index;
                }
            });
        } catch (e) {
            // Hello IE8
        }

        this.createInput();
        this.createResultsContainer();
        return this.container;
    },

    createInput: function () {
        this.input = L.DomUtil.create('input', 'photon-input', this.container);
        this.input.type = 'text';
        this.input.placeholder = this.options.placeholder;
        this.input.autocomplete = 'off';
        L.DomEvent.disableClickPropagation(this.input);

        L.DomEvent.on(this.input, 'keydown', this.onKeyDown, this);
        L.DomEvent.on(this.input, 'keyup', this.onKeyUp, this);
        L.DomEvent.on(this.input, 'blur', this.onBlur, this);
        L.DomEvent.on(this.input, 'focus', this.onFocus, this);
    },

    createResultsContainer: function () {
        this.resultsContainer = L.DomUtil.create('ul', 'photon-autocomplete', document.querySelector('body'));
    },

    resizeContainer: function()
    {
        var l = this.getLeft(this.input);
        var t = this.getTop(this.input) + this.input.offsetHeight;
        this.resultsContainer.style.left = l + 'px';
        this.resultsContainer.style.top = t + 'px';
        var width = this.options.width ? this.options.width : this.input.offsetWidth - 2;
        this.resultsContainer.style.width = width + "px";
    },

    onKeyDown: function (e) {
        switch (e.keyCode) {
            case this.KEYS.TAB:
                if(this.CURRENT !== null)
                {
                    this.setChoice();
                }
                L.DomEvent.stop(e);
                break;
            case this.KEYS.RETURN:
                L.DomEvent.stop(e);
                this.setChoice();
                break;
            case this.KEYS.ESC:
                L.DomEvent.stop(e);
                this.hide();
                this.input.blur();
                break;
            case this.KEYS.DOWN:
                if(this.RESULTS.length > 0) {
                    if(this.CURRENT !== null && this.CURRENT < this.RESULTS.length - 1) { // what if one resutl?
                        this.CURRENT++;
                        this.highlight();
                    }
                    else if(this.CURRENT === null) {
                        this.CURRENT = 0;
                        this.highlight();
                    }
                }
                break;
            case this.KEYS.UP:
                if(this.CURRENT !== null) {
                    L.DomEvent.stop(e);
                }
                if(this.RESULTS.length > 0) {
                    if(this.CURRENT > 0) {
                        this.CURRENT--;
                        this.highlight();
                    }
                    else if(this.CURRENT === 0) {
                        this.CURRENT = null;
                        this.highlight();
                    }
                }
                break;
        }
    },

    onKeyUp: function (e) {
        var special = [
            this.KEYS.TAB,
            this.KEYS.RETURN,
            this.KEYS.LEFT,
            this.KEYS.RIGHT,
            this.KEYS.DOWN,
            this.KEYS.UP,
            this.KEYS.APPLE,
            this.KEYS.SHIFT,
            this.KEYS.ALT,
            this.KEYS.CTRL
        ];
        if (special.indexOf(e.keyCode) === -1)
        {
            if (typeof this.submitDelay === "number") {
                window.clearTimeout(this.submitDelay);
                delete this.submitDelay;
            }
            this.submitDelay = window.setTimeout(L.Util.bind(this.search, this), this.options.submitDelay);
        }
    },

    onBlur: function (e) {
        this.fire('blur');
        var self = this;
        setTimeout(function () {
            self.hide();
        }, 100);
    },

    onFocus: function (e) {
        this.fire('focus');
        this.input.select();
    },

    clear: function () {
        this.RESULTS = [];
        this.CURRENT = null;
        this.CACHE = '';
        this.resultsContainer.innerHTML = '';
    },

    hide: function() {
        this.fire('hide');
        this.clear();
        this.resultsContainer.style.display = 'none';
    },

    setChoice: function (choice) {
        choice = choice || this.RESULTS[this.CURRENT];
        if (choice) {
            this.hide();
            this.input.value = "";
            this.fire('selected', {choice: choice.feature});
            this.onSelected(choice.feature);
        }
    },

    search: function() {
        var val = this.input.value;
        if (val.length < this.options.minChar) {
            this.clear();
            return;
        }
        if(!val) {
            this.clear();
            return;
        }
        if( val + '' === this.CACHE + '') {
            return;
        }
        else {
            this.CACHE = val;
        }
        this._do_search(val);
    },

    _do_search: function (val) {
        this.ajax(val, this.handleResults, this);
    },

    _onSelected: function (feature) {
        this.map.flyTo([feature.geometry.coordinates[1], feature.geometry.coordinates[0]], 8);
        waterproof.selectedCity = feature;
        if (this.options.selectedResultHandler) {
            this.options.selectedResultHandler(feature);
        }
        
    },

    onSelected: function (choice) {
        return (this.options.onSelected || this._onSelected).call(this, choice);
    },

    _formatResult: function (feature, el) {
        var title = L.DomUtil.create('strong', '', el),
            detailsContainer = L.DomUtil.create('small', '', el),
            details = [],
            type = this.formatType(feature);
        title.innerHTML = feature.properties.name;
        if (type) details.push(type);
        if (feature.properties.city && feature.properties.city !== feature.properties.name) {
            details.push(feature.properties.city);
        }
        if (feature.properties.country) details.push(feature.properties.country);
        detailsContainer.innerHTML = details.join(', ');
    },

    formatResult: function (feature, el) {
        return (this.options.formatResult || this._formatResult).call(this, feature, el);
    },

    formatType: function (feature) {
        return (this.options.formatType || this._formatType).call(this, feature);
    },

    _formatType: function (feature) {
        return feature.properties.osm_value;
    },

    createResult: function (feature) {
        var el = L.DomUtil.create('li', '', this.resultsContainer);
        this.formatResult(feature, el);
        var result = {
            feature: feature,
            el: el
        };
        // Touch handling needed
        L.DomEvent.on(el, 'mouseover', function (e) {
            this.CURRENT = result;
            this.highlight();
        }, this);
        L.DomEvent.on(el, 'mousedown', function (e) {
            this.setChoice();
        }, this);
        return result;
    },

    resultToIndex: function (result) {
        var out = null;
        this.forEach(this.RESULTS, function (item, index) {
            if (item === result) {
                out = index;
                return;
            }
        });
        return out;
    },

    handleResults: function(geojson) {
        var self = this;
        this.clear();
        this.resultsContainer.style.display = "block";
        this.resizeContainer();
        geojson.features = geojson.features.filter(feature => feature.properties.type=="city" || feature.properties.osm_value=="town");
        this.forEach(geojson.features, function (feature, index) {
            self.RESULTS.push(self.createResult(feature));
        });

        if (geojson.features.length === 0) {
            var noresult = L.DomUtil.create('li', 'photon-no-result', this.resultsContainer);
            noresult.innerHTML = this.options.noResultLabel;
        }
        
        this.CURRENT = 0;
        this.highlight();
        if (this.options.resultsHandler) {
            this.options.resultsHandler(geojson);
        }
    },

    highlight: function () {
        var self = this;
        this.forEach(this.RESULTS, function (item, index) {
            if (index === self.CURRENT) {
                L.DomUtil.addClass(item.el, 'on');
            }
            else {
                L.DomUtil.removeClass(item.el, 'on');
            }
        });
    },

    getLeft: function (el) {
        var tmp = el.offsetLeft;
        el = el.offsetParent;
        while(el) {
            tmp += el.offsetLeft;
            el = el.offsetParent;
        }
        return tmp;
    },

    getTop: function (el) {
        var tmp = el.offsetTop;
        el = el.offsetParent;
        while(el) {
            tmp += el.offsetTop;
            el = el.offsetParent;
        }
        return tmp;
    },

    forEach: function (els, callback) {
        Array.prototype.forEach.call(els, callback);
    },

    ajax: function (val, callback, thisobj) {
        if (typeof this.xhr === "object") {
            this.xhr.abort();
        }
        let filter_city = ""; // "&osm_tag=place:city";
        this.xhr = new XMLHttpRequest(),
            params = {
                q: val,
                lang: this.options.lang,
                limit: this.options.limit,
                bbox: this.toValidBBox(this.map.getBounds()),
            }, self = this;
        this.xhr.open('GET', this.options.url + this.buildQueryString(params) + filter_city, true);
        this.xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

        this.xhr.onload = function(e) {
            self.fire('ajax:return');
            if (this.status == 200) {
                if (callback) {
                    var raw = this.response;
                    raw = JSON.parse(raw);
                    callback.call(thisobj || this, raw);
                }
            }
            delete this.xhr;
        };

        this.fire('ajax:send');
        this.xhr.send();
    },

    buildQueryString: function (params) {
        var query_string = [];
        for (var key in params) {
            if (params[key]) {
                query_string.push(encodeURIComponent(key) + "=" + encodeURIComponent(params[key]));
            }
        }
        return query_string.join('%26');
    },

    toValidBBox: function(bbox){
        if (bbox.getWest() < -180 || bbox.getEast() > 180 || bbox.getNorth() > 90 || bbox.getSouth() < -90 ){
            return "-180,-90,180,90";
        }else{
            return bbox.toBBoxString();
        }

    }

});

L.Map.addInitHook(function () {
    if (this.options.photonControl) {
        this.photonControl = new L.Control.Photon(this.options.photonControlOptions || {});
        this.addControl(this.photonControl);
    }
});
