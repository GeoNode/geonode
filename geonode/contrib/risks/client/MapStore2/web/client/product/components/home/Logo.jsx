/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const logo1 = require('../../assets/img/mapstorelogo.png');
const logo2 = require('../../assets/img/MapStore2.png');

const Logo = React.createClass({
    render() {
        return (<div>
            <img src={logo1} className="mapstore-logo" />
            <img src={logo2} className="mapstore-logo" />
        </div>);
    }
});

module.exports = Logo;
