/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var {Col, Row} = require('react-bootstrap');
var I18N = require('../../../components/I18N/I18N');

const googleGroups = require('../../assets/img/groups_logo_sm.gif');
const LinkedinGroup = require('../../assets/img/linkedin_group.png');
const {Follow} = require('react-twitter-widgets');


var MailingLists = React.createClass({
    contextTypes: {
        messages: React.PropTypes.object
    },
    render() {
        return (
            <div id="mailinglists" className="container">
                <Row>
                    <Col>
                        <h1 className="color2" style={{align: "center", fontWeight: "bold", margin: "10px" }}><I18N.Message msgId="home.ml.title"/></h1>
                    </Col>
                </Row>
                <Row>
                    <Col sm={12} md={6}>
                        <table style={{padding: "5px", margin: "auto"}} cellSpacing="0">
                            <tbody>
                            <tr>
                                <td>
                                    <img src={googleGroups} height="30" width="136" alt="Google Groups" />
                                </td>
                            </tr>
                            <tr>
                                <td style={{paddingLeft: "10px", paddingRight: "10px"}}>
                                    <b><I18N.Message msgId="home.ml.subscribe_users"/></b>
                                </td>
                            </tr>
                            <tr>
                                <td style={{paddingLeft: "10px", paddingRight: "10px"}}>
                                    <form action="https://groups.google.com/group/mapstore-users/boxsubscribe">
                                        <I18N.Message msgId="home.ml.email"/> <input type="text" name="email" />
                                        <input type="submit" name="sub" value={this.context.messages.home.ml.subscribe} />
                                    </form>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <a className="link-white-bg" href="https://groups.google.com/group/mapstore-users"><I18N.Message msgId="home.ml.visit_group"/></a>
                                </td>
                            </tr>
                            </tbody>
                        </table>
                    </Col>
                    <Col sm={12} md={6}>
                        <table style={{padding: "5px", margin: "auto"}} cellSpacing="0">
                            <tbody>
                            <tr>
                                <td>
                                    <img src={googleGroups} height="30" width="136" alt="Google Groups" />
                                </td>
                            </tr>
                            <tr>
                                <td style={{paddingLeft: "10px", paddingRight: "10px"}}>
                                    <b><I18N.Message msgId="home.ml.subscribe_devel"/></b>
                                </td>
                            </tr>
                            <tr>
                                <td style={{paddingLeft: "10px", paddingRight: "10px"}}>
                                    <form action="https://groups.google.com/group/mapstore-developers/boxsubscribe">
                                        <I18N.Message msgId="home.ml.email"/> <input type="text" name="email" />
                                        <input type="submit" name="sub" value={this.context.messages.home.ml.subscribe} />
                                    </form>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <a className="link-white-bg" href="https://groups.google.com/group/mapstore-developers"><I18N.Message msgId="home.ml.visit_group"/></a>
                                </td>
                            </tr>
                            </tbody>
                        </table>
                    </Col>
                    <Col sm={12} md={6}>
                        <table style={{padding: "0", margin: "10px auto"}} cellSpacing="0">
                            <tbody>
                            <tr>
                                <td>
                                    <img style={{
                                            background: "white",
                                            borderRadius: "2px 2px 2px 2px"
                                        }} src={LinkedinGroup} height="50" width="100" alt="Linkedin Groups" />
                                </td>
                            </tr>
                            <tr>
                                <td style={{paddingLeft: "10px", paddingRight: "10px"}}>
                                    <b><I18N.Message msgId="home.LinkedinGroup"/></b>
                                </td>
                            </tr>
                            <tr>
                                <td style={{padding: "10px"}}>
                                    <a className="link-white-bg" href="https://www.linkedin.com/groups/7444734/profile"><I18N.Message msgId="home.ml.visit_group"/></a>
                                </td>
                            </tr>
                            </tbody>
                        </table>
                    </Col>
                    <Col sm={12} md={6} style={{padding: "50px 10px"}}>
                        <Follow options={{size: 'large'}} username="mapstore2" />
                    </Col>
                </Row>
			</div>
        );
    }
});

module.exports = MailingLists;
