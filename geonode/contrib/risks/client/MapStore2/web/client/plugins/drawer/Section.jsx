/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');

var {Glyphicon, Modal} = require('react-bootstrap');
const assign = require('object-assign');

var Section = React.createClass({
    propTypes: {
        key: React.PropTypes.string,
        eventKey: React.PropTypes.string,
        headerClassName: React.PropTypes.string,
        open: React.PropTypes.bool,
        onHeaderClick: React.PropTypes.func,
        renderInModal: React.PropTypes.bool,
        header: React.PropTypes.node
    },
    getDefaultProps() {
        return {
            headerClassName: 'panel-heading'
        };
    },
    onHeaderClick() {
        this.props.onHeaderClick(this.props.eventKey);
    },
    onModalClose() {
        this.setProps(assign(this.props, {open: false}));
    },
    getHeight() {
        if (this.props.open && this.refs.sectionContent) {
            return this.refs.sectionContent.scrollHeight + 10;
        }
        return "0";
    },
    render() {
        var style = {
            maxHeight: this.getHeight(),
            overflow: this.props.open ? "auto" : "hidden",
            padding: !this.props.open ? "0" : null
        };
        return (
            <div className={"section"}>
                <div className="sectionHeader" style={{width: "100%"}} onClick={this.onHeaderClick}>
                    { !this.props.renderInModal ? <Glyphicon glyph="triangle-right" style={this.props.open ? {transform: "rotate(90deg)"} : {} } /> : null }
                    <span className={this.headerClassName + " sectionTitle"} ref="sectionTitle" >{this.props.header}</span>
                </div>
                {!this.props.renderInModal ?
                     <div ref="sectionContent" className="sectionContent" style={style} >{this.props.children}</div>
                         :
                     (<Modal ref="modal" show={this.props.open}
                         onHide={this.onHeaderClick}>
                        <Modal.Header closeButton >
                         <Modal.Title>{this.props.header}</Modal.Title>
                     </Modal.Header>
                     <Modal.Body>{this.props.children}</Modal.Body></Modal>)}
            </div>
        );
    }

});
module.exports = Section;
