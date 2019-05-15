/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var I18N = require('../../../../components/I18N/I18N');
var gsLogo = require('../../../assets/img/geosolutions-brand.png');
var msLogo = require('../../../assets/img/mapstore-logo-0.20.png');

var About = React.createClass({

    render() {
        return (
                <div style={{
                    backgroundImage: 'url("' + msLogo + '")',
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'center'
                }}>
                    <h1>MapStore 2</h1>
                    <p>
                        <I18N.Message msgId="about_p0-0"/> <a href="http://openlayers.org/">OpenLayers 3</a> <I18N.Message msgId="about_p0-1"/> <a href="http://leafletjs.com/">Leaflet</a>.
                    </p>
                    <p><I18N.Message msgId="about_p1"/></p>
                    <ul>
                        <li>
                            <I18N.Message msgId="about_ul0_li0"/>
                        </li>
                        <li>
                            <I18N.Message msgId="about_ul0_li1"/> <a href="https://github.com/geosolutions-it/MapStore2/wiki">MapStore wiki</a>.
                        </li>
                    </ul>
                    <h2><I18N.Message msgId="about_h20"/></h2>
                    <p>
                        <I18N.Message msgId="about_p3"/>
                    </p>
                    <p><I18N.Message msgId="about_p5-0"/> <a href="https://github.com/geosolutions-it/MapStore2/blob/master/CONTRIBUTING.md"><I18N.Message msgId="about_a0"/></a> <I18N.Message msgId="about_p5-1"/></p>
                    <h3><I18N.Message msgId="about_h21"/></h3>
                    <p><I18N.Message msgId="about_p6"/></p>
                    <a href="http://www.geo-solutions.it/">
                        <img
                            src={gsLogo}
                            style={{
                                display: "block",
                                margin: "auto",
                                maxWidth: "100%"
                            }}
                            alt="GeoSolutions S.A.S.">
                        </img>
                    </a>
                </div>);
    }
});

module.exports = About;
