/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Button, Glyphicon} = require('react-bootstrap');
const ReactPDF = require('react-pdf').default;

const PrintPreview = React.createClass({
    propTypes: {
        url: React.PropTypes.string,
        scale: React.PropTypes.number,
        currentPage: React.PropTypes.number,
        pages: React.PropTypes.number,
        zoomFactor: React.PropTypes.number,
        minScale: React.PropTypes.number,
        maxScale: React.PropTypes.number,
        back: React.PropTypes.func,
        setScale: React.PropTypes.func,
        setPage: React.PropTypes.func,
        setPages: React.PropTypes.func,
        style: React.PropTypes.object,
        buttonStyle: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            url: null,
            scale: 1.0,
            minScale: 0.25,
            maxScale: 8.0,
            currentPage: 0,
            pages: 1,
            zoomFactor: 2.0,
            back: () => {},
            setScale: () => {},
            setPage: () => {},
            setPages: () => {},
            style: {height: "500px", width: "800px", overflow: "auto", backgroundColor: "#888", padding: "10px"},
            buttonStyle: "default"
        };
    },
    onDocumentComplete(pages) {
        this.props.setPages(pages && pages.total || 0);
    },
    render() {
        if (window.PDFJS) {
            return (
                <div>
                    <div style={this.props.style}>
                        <ReactPDF file={this.props.url} scale={this.props.scale} pageIndex={this.props.currentPage} onDocumentLoad={this.onDocumentComplete}/>
                    </div>
                    <div style={{marginTop: "10px"}}>
                        <Button bsStyle={this.props.buttonStyle} style={{marginRight: "10px"}} onClick={this.props.back}><Glyphicon glyph="arrow-left"/></Button>
                        <Button bsStyle={this.props.buttonStyle} disabled={this.props.scale >= this.props.maxScale} onClick={this.zoomIn}><Glyphicon glyph="zoom-in"/></Button>
                        <Button bsStyle={this.props.buttonStyle} disabled={this.props.scale <= this.props.minScale} onClick={this.zoomOut}><Glyphicon glyph="zoom-out"/></Button>
                        <label style={{marginLeft: "10px", marginRight: "10px"}}>{this.props.scale}x</label>
                        <div className={"print-download btn btn-" + this.props.buttonStyle}><a href={this.props.url} target="_blank"><Glyphicon glyph="save"/></a></div>
                        <Button bsStyle={this.props.buttonStyle} disabled={this.props.currentPage === 0} onClick={this.firstPage}><Glyphicon glyph="step-backward"/></Button>
                        <Button bsStyle={this.props.buttonStyle} disabled={this.props.currentPage === 0} onClick={this.prevPage}><Glyphicon glyph="chevron-left"/></Button>
                        <label style={{marginLeft: "10px", marginRight: "10px"}}>{this.props.currentPage + 1} / {this.props.pages}</label>
                        <Button bsStyle={this.props.buttonStyle} disabled={this.props.currentPage === this.props.pages - 1} onClick={this.nextPage}><Glyphicon glyph="chevron-right"/></Button>
                        <Button bsStyle={this.props.buttonStyle} disabled={this.props.currentPage === this.props.pages - 1} onClick={this.lastPage}><Glyphicon glyph="step-forward"/></Button>
                    </div>
                </div>
            );
        }
        return null;
    },
    firstPage() {
        if (this.props.currentPage > 0) {
            this.props.setPage(0);
        }
    },
    lastPage() {
        if (this.props.currentPage < this.props.pages - 1 ) {
            this.props.setPage(this.props.pages - 1);
        }
    },
    prevPage() {
        if (this.props.currentPage > 0) {
            this.props.setPage(this.props.currentPage - 1);
        }
    },
    nextPage() {
        if (this.props.currentPage < this.props.pages - 1) {
            this.props.setPage(this.props.currentPage + 1);
        }
    },
    zoomIn() {
        this.props.setScale(this.props.scale * this.props.zoomFactor);
    },
    zoomOut() {
        this.props.setScale(this.props.scale / this.props.zoomFactor);
    }
});

module.exports = PrintPreview;
