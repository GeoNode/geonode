/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const Message = require('../locale/Message');

const {ShapeFileUploadAndStyle, StylePolygon, StylePolyline, StylePoint} = require('./index');

const {Glyphicon, Panel} = require('react-bootstrap');

const Dialog = require('../../components/misc/Dialog');

require('./css/shapeFile.css');
const ShapeFile = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        layers: React.PropTypes.array,
        selected: React.PropTypes.object,
        style: React.PropTypes.object,
        shapeStyle: React.PropTypes.object,
        onShapeError: React.PropTypes.func,
        onShapeChoosen: React.PropTypes.func,
        addShapeLayer: React.PropTypes.func,
        shapeLoading: React.PropTypes.func,
        onSelectLayer: React.PropTypes.func,
        onLayerAdded: React.PropTypes.func,
        error: React.PropTypes.string,
        mapType: React.PropTypes.string,
        wrap: React.PropTypes.bool,
        wrapWithPanel: React.PropTypes.bool,
        panelStyle: React.PropTypes.object,
        panelClassName: React.PropTypes.string,
        visible: React.PropTypes.bool,
        toggleControl: React.PropTypes.func,
        closeGlyph: React.PropTypes.string,
        buttonSize: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            id: "mapstore-shapefile-upload",
            wrap: true,
            wrapWithPanel: false,
            panelStyle: {
                minWidth: "360px",
                zIndex: 100,
                position: "absolute",
                overflow: "visible",
                top: "100px",
                left: "calc(50% - 150px)"
            },
            panelClassName: "toolbar-panel",
            visible: false,
            toggleControl: () => {},
            closeGlyph: "1-close",
            buttonSize: "small"
        };
    },
    render() {
        const stylers = {
            Polygon: <StylePolygon/>,
            MultiPolygon: <StylePolygon/>,
            LineString: <StylePolyline/>,
            MultiLineString: <StylePolyline/>,
            MultiPoint: <StylePoint/>,
            Point: <StylePoint/>
        };
        const panel = (<ShapeFileUploadAndStyle role="body" {...this.props} stylers={stylers}
            uploadMessage={<Message msgId="shapefile.placeholder"/>}
            cancelMessage={<Message msgId="shapefile.cancel"/>}
            addMessage={<Message msgId="shapefile.add"/>}
            />);

        if (this.props.wrap) {
            if (this.props.visible) {
                if (this.props.wrapWithPanel) {
                    return (<Panel id={this.props.id} header={<span><span className="shapefile-panel-title"><Message msgId="shapefile.title"/></span><span className="shapefile-panel-close panel-close" onClick={this.props.toggleControl}></span></span>} style={this.props.panelStyle} className={this.props.panelClassName}>
                        {panel}
                    </Panel>);
                }
                return (<Dialog id={this.props.id} style={this.props.panelStyle} className={this.props.panelClassName}>
                    <span role="header">
                        <span className="shapefile-panel-title"><Message msgId="shapefile.title"/></span>
                        <button onClick={this.props.toggleControl} className="shapefile-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>�</span>}</button>
                    </span>
                    {panel}
                </Dialog>);
            }
            return null;
        }
        return panel;
    }
});

module.exports = ShapeFile;
