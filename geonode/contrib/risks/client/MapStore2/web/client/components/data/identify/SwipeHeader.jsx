/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const {Glyphicon, Button} = require('react-bootstrap');
require('./css/swipeHeader.css');

const SwipeHeader = React.createClass({
    propTypes: {
        title: React.PropTypes.string,
        index: React.PropTypes.number,
        size: React.PropTypes.number,
        container: React.PropTypes.oneOfType([React.PropTypes.object, React.PropTypes.func]),
        useButtons: React.PropTypes.bool,
        onPrevious: React.PropTypes.func,
        onNext: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            useButtons: true
        };
    },
    componentWillUnmount() {
        if (this.interval) {
            clearInterval(this.interval);
        }
    },
    renderLeftButton() {
        return this.props.useButtons ?
            <Button ref="left" disabled={this.props.index === 0 ? true : false} className="swipe-header-left-button square-button" bsStyle="primary" onClick={() => {this.props.onPrevious(); }}><Glyphicon glyph="arrow-left"/></Button> :
            <a ref="left" disabled={this.props.index === 0 ? true : false} className="swipe-header-left-button" onClick={() => {this.props.onPrevious(); }}><Glyphicon glyph="chevron-left" /></a>;
    },
    renderRightButton() {
        return this.props.useButtons ?
            <Button ref="right" disabled={this.props.index === (this.props.size - 1) ? true : false } className="swipe-header-right-button square-button" bsStyle="primary" onClick={() => {this.props.onNext(); }}><Glyphicon glyph="arrow-right"/></Button> :
            <a ref="right" disabled={this.props.index === (this.props.size - 1) ? true : false} className="swipe-header-right-button" onClick={() => {this.props.onNext(); }}><Glyphicon glyph="chevron-right" /></a>;
    },
    render() {
        return (<span>{this.renderLeftButton()} <span>{this.props.title}</span> {this.renderRightButton()}</span>);
    }
});

module.exports = SwipeHeader;
