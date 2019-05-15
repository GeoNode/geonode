/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const src = require("./attribution/geosolutions-brand.png");
require('./footer/footer.css');

const Footer = React.createClass({
    render() {
        return (
            <div className="ms-footer col-md-12">
            <div><a target="_blank" href="http://www.geo-solutions.it/"> <img src={src} width="140" title="GeoSolutions" alt="GeoSolutions" /></a> <br/><br/></div>
                GeoSolutions S.a.s. | Via Poggio alle Viti, 1187 - 55054 Massarosa (Lucca) - Italy
                info@geo-solutions.it | Tel: +39 0584 962313 | Fax: +39 0584 1660272
            </div>
        );
    }
});

module.exports = {
    FooterPlugin: Footer
};
