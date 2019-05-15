/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const img = require('../../assets/img/mwlii.png');

const MadeWithLove = React.createClass({
    render() {
        return (<div id="mapstore-madewithlove" ><img src={img} /></div>);
    }
});
module.exports = MadeWithLove;
