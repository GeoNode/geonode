/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const Debug = require('../../MapStore2/web/client/components/development/Debug');
const {connect} = require('react-redux');


const {Link} = require('react-router');

const {Glyphicon} = require('react-bootstrap');

const Home = () => (
    (<div>
        <div className="homepage">
            <div className="header">
                <div className="header-text">
                    Title
                </div>
                <div className="header-burger">
                    <Glyphicon glyph="glyphicon glyphicon-menu-hamburger"/>
                </div>
            </div>
            <div className="main-home">
                <Link to="/main">
                    <p><span style={{"color": "#808080", "fontSize": "16px"}}>MAIN</span></p>
                </Link>
            </div>
        </div>
        <Debug/>
    </div>)
);

module.exports = connect((state) => {
    return {
        error: state.loadingError || (state.locale && state.locale.localeError) || null,
        locale: state.locale && state.locale.locale,
        messages: state.locale && state.locale.messages || {}
    };
})(Home);
