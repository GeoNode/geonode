/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');

const {Grid, Row, Col, Panel, PanelGroup, Button, Glyphicon} = require('react-bootstrap');

const Combobox = require('react-widgets').Combobox;

const {getWindowSize} = require('../utils/AgentUtils');
const {setRasterStyleParameter, setRasterLayer} = require('../actions/rasterstyler');
const {changeLayerProperties} = require('../actions/layers');

const {
    RedBandSelector,
    BlueBandSelector,
    GreenBandSelector,
    GrayBandSelector,
    PseudoBandSelector,
    RasterStyleTypePicker,
    EqualInterval,
    PseudoColor,
    OpacityPicker
} = require('./rasterstyler/index');

const {layersSelector} = require('../selectors/layers');

const {createSelector} = require('reselect');

const assign = require('object-assign');

require('./rasterstyler/rasterstyler.css');

const Message = require('./locale/Message');

const {jsonToSLD} = require("../utils/SLDUtils");

const RasterStyler = React.createClass({
    propTypes: {
        layers: React.PropTypes.array,
        layer: React.PropTypes.object,
        styletype: React.PropTypes.oneOf(['rgb', 'gray', 'pseudo']),
        opacity: React.PropTypes.string,
        withContainer: React.PropTypes.bool,
        open: React.PropTypes.bool,
        forceOpen: React.PropTypes.bool,
        style: React.PropTypes.object,
        selectLayer: React.PropTypes.func,
        setRasterStyleParameter: React.PropTypes.func,
        error: React.PropTypes.string,
        rasterstyler: React.PropTypes.object,
        changeLayerProperties: React.PropTypes.func,
        hideLayerSelector: React.PropTypes.bool

    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            open: false,
            forceOpen: false,
            layers: [],
            layer: null,
            withContainer: true,
            selectLayer: () => {},
            setRasterStyleParameter: () => {},
            styletype: "pseudo",
            opacity: "1.00",
            style: {},
            rasterstyler: {},
            changeLayerProperties: () => {},
            hideLayerSelector: false
        };
    },
    componentWillMount() {
    },
    componentWillUpdate(nextProps) {
        this.bands = nextProps.layer && nextProps.layer.describeLayer ? nextProps.layer.describeLayer.bands : undefined;

    },
    getPanelStyle() {
        let size = getWindowSize();
        let maxHeight = size.maxHeight - 10;
        let maxWidth = size.maxWidth - 70;
        let style = {maxHeight: maxHeight, maxWidth: maxWidth};
        if ( maxHeight < 600 ) {
            style.height = maxHeight;
            style.overflowY = "auto";
        }
        return style;
    },
    renderError() {
        if (this.props.error) {
            return <Row><Col xs={12}><div className="rasterstyler-error"><span>{this.props.error}</span></div></Col></Row>;
        }
        return null;
    },
    renderWarning(layout) {
        if (!layout) {
            return <Row><Col xs={12}><div className="rasterstyler-warning"><span><Message msgId="print.layoutWarning"/></span></div></Col></Row>;
        }
        return null;
    },
    renderSelector() {
        return (<Row style={{marginBottom: "22px"}}>
                    <Row>
                       {!this.props.hideLayerSelector ? ( <Col xs={4} >
                            <label><Message msgId="rasterstyler.layerlabel"/></label>
                            <Combobox data={this.props.layers.reverse()}
                                value={(this.props.layer) ? this.props.layer.id : null}
                                onChange={(value)=> this.props.selectLayer(value)}
                                valueField={"id"}
                                textField={"title"} />
                        </Col>) : null }
                        {this.props.layer ? (<Col xs={4}>
                            <label><Message msgId="rasterstyler.typelabel"/></label>
                            <RasterStyleTypePicker styletype={this.props.styletype}/> </Col>) : null}
                        {this.props.layer ? (<Col xs={4} style={{paddingRight: "27px", "paddingTop": "7px"}}>
                            <label><Message msgId="rasterstyler.opacitylabel"/></label>
                            <OpacityPicker disabled={this.canApply()} opacity={this.props.opacity}/>
                         </Col>) : null}
                    </Row>
                </Row>);
    },
    renderRasterStyler() {
        return this.props.layer ? (
            <Row>
                    {(this.props.styletype === 'gray') ? this.renderGreyscale() : null}
                    {(this.props.styletype === 'rgb') ? this.renderRGB() : null}
                    {(this.props.styletype === 'pseudo') ? this.renderPseudocolor() : null}
            </Row>) : null;
    },
    renderRGB() {
        return (<PanelGroup defaultActiveKey="1" accordion>
                    <Panel header={(<label><Message msgId="rasterstyler.redtitle"/></label>)} eventKey="1">
                        <RedBandSelector bands={this.bands}/>
                    </Panel>
                    <Panel header={(<label><Message msgId="rasterstyler.greentitle"/></label>)} eventKey="2">
                        <GreenBandSelector bands={this.bands}/>
                    </Panel>
                    <Panel header={(<label><Message msgId="rasterstyler.bluetitle"/></label>)} eventKey="3">
                        <BlueBandSelector bands={this.bands}/>
                    </Panel>
                </PanelGroup> );
    },
    renderGreyscale() {
        return (
            <Panel header={(<label><Message msgId="rasterstyler.graytitle"/></label>)} eventKey="1">
                <GrayBandSelector bands={this.bands}/>
            </Panel>);
    },
    renderPseudocolor() {
        return (
            <PanelGroup activeKey={this.props.rasterstyler.pseudocolor.activepanel}
                onSelect={(activeKey) => this.props.setRasterStyleParameter("pseudocolor", "activepanel", activeKey)}
                accordion>
                <Panel header={(<label><Message msgId="rasterstyler.pseudobandtitle"/></label>)} eventKey="3">
                    <PseudoBandSelector bands={(this.bands) ? ["none"].concat(this.bands) : ["none", "1", "2", "3"]} />
                </Panel>
                <Panel header={(<label><Message msgId="rasterstyler.eqinttitle"/></label>)}
                    eventKey="1">
                    <EqualInterval onClassify={this.classify}/>
                </Panel>
                 <Panel header={(<label><Message msgId="rasterstyler.pseudotitle"/></label>)}
                    eventKey="2">
                    {this.props.rasterstyler.pseudocolor.activepanel === "2" ? (<PseudoColor/>) : null}
                 </Panel>
            </PanelGroup>
        );
    },
    renderApplyBtn() {
        return (
            <Row><Button style={{"float": "right"}} onClick={this.apply}
            disabled={this.canApply()} ><Message msgId="rasterstyler.applybtn"/></Button></Row>);
    },
    renderBody() {

        return (<Grid fluid>
                {this.renderError()}
                {this.renderSelector()}
                {this.renderRasterStyler()}
                {this.props.layer ? this.renderApplyBtn() : null}
                </Grid>);
    },
    render() {
        if (this.props.forceOpen || this.props.open) {
            return this.props.withContainer ?
                (<Panel className="mapstore-rasterstyler-panel"
                        style={this.getPanelStyle()}
                        header={<label><Message msgId="rasterstyler.paneltitle"/></label>}>
                        {this.renderBody()}
                </Panel>) : this.renderBody();
        }
        return null;
    },
    classify(prop, colorMap) {
        let newColorMapEntry = colorMap.map((entry) => {
            entry.label = entry.quantity.toFixed(2);
            return entry;
        });
        this.props.setRasterStyleParameter("pseudocolor", "activepanel", "2");
        this.props.setRasterStyleParameter("pseudocolor", "colorMapEntry", newColorMapEntry);
    },
    apply() {
        let style = jsonToSLD({
            styletype: this.props.styletype,
            opacity: this.props.opacity,
            state: this.props.rasterstyler,
            layer: this.props.layer});
        this.props.changeLayerProperties(this.props.layer.id, { params: assign({}, this.props.layer.params, {SLD_BODY: style})});
    },
    canApply() {
        let rstyler = this.props.rasterstyler;
        let entryLength = 0;
        if (rstyler && rstyler.pseudocolor) {
            entryLength = (rstyler.pseudocolor.type === "ramp" || rstyler.pseudocolor.type === "intervals") ? 1 : 0;
        }

        let disabled = (this.props.styletype === 'pseudo' && this.props.rasterstyler.pseudocolor.colorMapEntry.length <= entryLength) ? true : false;
        return disabled;
    }
});
const selector = createSelector([
    (state) => (state.controls.toolbar && state.controls.toolbar.active === 'rasterstyler'),
    (state) => state.rasterstyler && state.rasterstyler.layer,
    (state) => state.rasterstyler && state.rasterstyler.typepicker && state.rasterstyler.typepicker.styletype,
    (state) => state.rasterstyler && state.rasterstyler.opacitypicker && state.rasterstyler.opacitypicker.opacity,
    layersSelector,
    (state) => state.rasterstyler
], (open, layer, styletype, opacity, layers, rasterstyler) => ({
    open,
    layer,
    styletype,
    opacity,
    layers: layers.filter((l) => { return l.group !== 'background'; }),
    rasterstyler
}));

const RasterStylerPlugin = connect(selector, {
        setRasterStyleParameter: setRasterStyleParameter,
        selectLayer: setRasterLayer,
        changeLayerProperties: changeLayerProperties
    })(RasterStyler);

module.exports = {
    RasterStylerPlugin: assign( RasterStylerPlugin,
        {
        Toolbar: {
            name: 'rasterstyler',
            help: <Message msgId="helptexts.rasterstyler"/>,
            tooltip: "rasterstyler.tooltip",
            icon: <Glyphicon glyph="pencil"/>,
            position: 9,
            panel: true,
            exclusive: true
        }
    }),
    reducers: {rasterstyler: require('../reducers/rasterstyler')}
};
