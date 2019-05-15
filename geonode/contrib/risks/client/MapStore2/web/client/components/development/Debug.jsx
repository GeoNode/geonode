/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var url = require('url');
if (!global.Symbol) {
    require("babel-polyfill");
}

const urlQuery = url.parse(window.location.href, true).query;

let Debug = React.createClass({
    render() {
        if (__DEVTOOLS__ && urlQuery.debug && !window.devToolsExtension) {
            const DevTools = require('./DevTools');
            return (
                <DevTools/>
            );
        }
        return null;
    }
});

module.exports = Debug;
