!function(e){if("object"==typeof exports)module.exports=e();else if("function"==typeof define&&define.amd)define(e);else{var f;"undefined"!=typeof window?f=window:"undefined"!=typeof global?f=global:"undefined"!=typeof self&&(f=self),f.tokml=e()}}(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var strxml = require('strxml'),
    tag = strxml.tag,
    encode = strxml.encode;

module.exports = function tokml(geojson, options) {

    options = options || {
        documentName: undefined,
        documentDescription: undefined,
        name: 'name',
        description: 'description',
        simplestyle: false
    };

    return '<?xml version="1.0" encoding="UTF-8"?>' +
        tag('kml',
            tag('Document',
                documentName(options) +
                documentDescription(options) +
                root(geojson, options)
               ), [['xmlns', 'http://www.opengis.net/kml/2.2']]);
};

function feature(options) {
    return function(_) {
        var styleDefinition = '',
            styleReference = '';
        if (options.simplestyle && hasStyle(_.properties)) {
            styleDefinition = iconstyle(_.properties);
            styleReference = tag('styleUrl', '#' + iconHash(_.properties));
        }
        if (!_.properties || !geometry.valid(_.geometry)) return '';
        var geometryString = geometry.any(_.geometry);
        if (!geometryString) return '';
        return styleDefinition + tag('Placemark',
            name(_.properties, options) +
            description(_.properties, options) +
            geometryString +
            extendeddata(_.properties) +
            styleReference);
    };
}

function root(_, options) {
    if (!_.type) return '';
    switch (_.type) {
        case 'FeatureCollection':
            if (!_.features) return '';
            return _.features.map(feature(options)).join('');
        case 'Feature':
            return feature(options)(_);
        default:
            return feature(options)({
                type: 'Feature',
                geometry: _,
                properties: {}
            });
    }
    return '';
}

function documentName(options) {
    return (options.documentName !== undefined) ? tag('name', options.documentName) : '';
}

function documentDescription(options) {
    return (options.documentDescription !== undefined) ? tag('description', options.documentDescription) : '';
}

function name(_, options) {
    return _[options.name] ? tag('name', encode(_[options.name])) : '';
}

function description(_, options) {
    return _[options.description] ? tag('description', encode(_[options.description])) : '';
}

// ## Geometry Types
//
// https://developers.google.com/kml/documentation/kmlreference#geometry
var geometry = {
    Point: function(_) {
        return tag('Point', tag('coordinates', _.coordinates.join(',')));
    },
    LineString: function(_) {
        return tag('LineString', tag('coordinates', linearring(_.coordinates)));
    },
    Polygon: function(_) {
        if (!_.coordinates.length) return '';
        var outer = _.coordinates[0],
            inner = _.coordinates.slice(1),
            outerRing = tag('outerBoundaryIs',
                tag('LinearRing', tag('coordinates', linearring(outer)))),
            innerRings = inner.map(function(i) {
                return tag('innerBoundaryIs',
                    tag('LinearRing', tag('coordinates', linearring(i))));
            }).join('');
        return tag('Polygon', outerRing + innerRings);
    },
    MultiPoint: function(_) {
        if (!_.coordinates.length) return '';
        return tag('MultiGeometry', _.coordinates.map(function(c) {
            return geometry.Point({ coordinates: c });
        }).join(''));
    },
    MultiPolygon: function(_) {
        if (!_.coordinates.length) return '';
        return tag('MultiGeometry', _.coordinates.map(function(c) {
            return geometry.Polygon({ coordinates: c });
        }).join(''));
    },
    MultiLineString: function(_) {
        if (!_.coordinates.length) return '';
        return tag('MultiGeometry', _.coordinates.map(function(c) {
            return geometry.LineString({ coordinates: c });
        }).join(''));
    },
    GeometryCollection: function(_) {
        return tag('MultiGeometry',
            _.geometries.map(geometry.any).join(''));
    },
    valid: function(_) {
        return _ && _.type && (_.coordinates ||
            _.type === 'GeometryCollection' && _.geometries.every(geometry.valid));
    },
    any: function(_) {
        if (geometry[_.type]) {
            return geometry[_.type](_);
        } else {
            return '';
        }
    }
};

function linearring(_) {
    return _.map(function(cds) { return cds.join(','); }).join(' ');
}

// ## Data
function extendeddata(_) {
    return tag('ExtendedData', pairs(_).map(data).join(''));
}

function data(_) {
    return tag('Data', tag('value', encode(_[1])), [['name', encode(_[0])]]);
}

// ## Icons
function iconstyle(_) {
    return tag('Style',
        tag('IconStyle',
            tag('Icon',
                tag('href', iconUrl(_)))) +
        iconSize(_), [['id', iconHash(_)]]);
}

function iconUrl(_) {
    var size = _['marker-size'] || 'medium',
        symbol = _['marker-symbol'] ? '-' + _['marker-symbol'] : '',
        color = (_['marker-color'] || '7e7e7e').replace('#', '');

    return 'https://api.tiles.mapbox.com/v3/marker/' + 'pin-' + size.charAt(0) +
        symbol + '+' + color + '.png';
}

function iconSize(_) {
    return tag('hotSpot', '', [
        ['xunits', 'fraction'],
        ['yunits', 'fraction'],
        ['x', 0.5],
        ['y', 0.5]
    ]);
}

function hasStyle(_) {
    return !!(_['marker-size'] || _['marker-symbol'] || _['marker-color']);
}

function iconHash(_) {
    return (_['marker-symbol'] || '') +
        (_['marker-color'] || '').replace('#', '') +
        (_['marker-size'] || '');
}

// ## Helpers
function pairs(_) {
    var o = [];
    for (var i in _) o.push([i, _[i]]);
    return o;
}

},{"strxml":2}],2:[function(require,module,exports){
module.exports.attr = attr;
module.exports.tagClose = tagClose;
module.exports.tag = tag;
module.exports.encode = encode;

/**
 * @param {array} _ an array of attributes
 * @returns {string}
 */
function attr(_) {
    return (_ && _.length) ? (' ' + _.map(function(a) {
        return a[0] + '="' + a[1] + '"';
    }).join(' ')) : '';
}

/**
 * @param {string} el element name
 * @param {array} attributes array of pairs
 * @returns {string}
 */
function tagClose(el, attributes) {
    return '<' + el + attr(attributes) + '/>';
}

/**
 * @param {string} el element name
 * @param {string} contents innerXML
 * @param {array} attributes array of pairs
 * @returns {string}
 */
function tag(el, contents, attributes) {
    return '<' + el + attr(attributes) + '>' + contents + '</' + el + '>';
}

/**
 * @param {string} _ a string of attribute
 * @returns {string}
 */
function encode(_) {
    return (_ === null ? '' : _.toString()).replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

},{}]},{},[1])
(1)
});