/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {Grid, Row, Col} = require('react-bootstrap');
const Examples = require('../components/home/Examples');
const MailingLists = require('../components/home/MailingLists');

const ExamplesPlugin = React.createClass({
    render() {
        return (<Grid fluid>
            <Row className="show-grid">
                <Col xs={12} lg={6}>
                    <Examples/>
                </Col>
                <Col xs={12} lg={6}>
                    <MailingLists/>
                </Col>
            </Row>
        </Grid>
        );
    }
});

module.exports = {
    ExamplesPlugin: ExamplesPlugin
};
