/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var MailingLists = require('./MailingLists');
const MadeWithLove = require('../../assets/img/mwlii.png');

var Footer = React.createClass({
    render() {
        return (
            <div id="footer" style={{
                textAlign: "center"
            }}>
                <MailingLists/>
                <br></br>
                <img src={MadeWithLove} />
                <p align="center"><b><a href="http://www.geo-solutions.it">GeoSolutions s.a.s.</a></b> • Via Poggio alle Viti 1187 - 55054 Massarosa (Lucca) - Italy</p>
                <p align="center"><a href="mailto:info@geo-solutions.it">info@geo-solutions.it</a> • <a href="http://www.geo-solutions.it">www.geo-solutions.it</a> • Tel: 0039 0584 962313 • Fax: 0039 0584 1660272</p>
            </div>
        );
    }
});

module.exports = Footer;
