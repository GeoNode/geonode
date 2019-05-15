/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');

const {Grid, Row, Col, Panel, PanelGroup, Button, Glyphicon, FormControl} = require('react-bootstrap');

const Combobox = require('react-widgets').Combobox;

const {getWindowSize} = require('../utils/AgentUtils');
const {
    setVectorStyleParameter,
    setVectorLayer,
    newVectorRule,
    selectVectorRule,
    removeVectorRule,
    setVectorRuleParameter} = require('../actions/vectorstyler');
const {changeLayerProperties} = require('../actions/layers');
const {
    StylePolygon,
    StylePolyline,
    StylePoint,
    ScaleDenominator} = require('./vectorstyler/index');

const {layersSelector} = require('../selectors/layers');
const {ruleselctor} = require('../selectors/vectorstyler');

const {createSelector} = require('reselect');

const assign = require('object-assign');

require('./vectorstyler/vectorstyler.css');

const Message = require('./locale/Message');

const {vecStyleToSLD} = require("../utils/SLDUtils");

const VectorStyler = React.createClass({
    propTypes: {
        layers: React.PropTypes.array,
        layer: React.PropTypes.object,
        rules: React.PropTypes.array,
        rule: React.PropTypes.object,
        withContainer: React.PropTypes.bool,
        open: React.PropTypes.bool,
        forceOpen: React.PropTypes.bool,
        style: React.PropTypes.object,
        selectLayer: React.PropTypes.func,
        setVectorStyleParameter: React.PropTypes.func,
        addRule: React.PropTypes.func,
        removeRule: React.PropTypes.func,
        selectRule: React.PropTypes.func,
        setRuleParameter: React.PropTypes.func,
        error: React.PropTypes.string,
        changeLayerProperties: React.PropTypes.func,
        hideLayerSelector: React.PropTypes.bool

    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getInitialState() {
        return {

        };
    },
    getDefaultProps() {
        return {
            hideLayerSelector: false,
            open: false,
            layers: [],
            layer: null,
            forceOpen: false,
            withContainer: true,
            selectLayer: () => {},
            setVectorStyleParameter: () => {},
            opacity: "1.00",
            style: {},
            changeLayerProperties: () => {},
            addRule: () => {},
            removeRule: () => {},
            selectRule: () => {},
            setRuleParameter: () => {}
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
    renderStyle() {
        switch (this.props.layer.describeLayer.geometryType) {
            case 'Polygon':
            case 'MultiPolygon':
            case 'MultiSurface': {
                return (<StylePolygon/>);
            }
            case 'LineString':
            case 'MultiLineString':
            {
                return (<StylePolyline/>);
            }
            case 'Point':
            case 'MultiPoint': {
                return (<StylePoint showMarker={false} showMarkSelector={true}/>);
            }
            default: {
                return null;
            }
        }
    },
    renderSymbolStyler() {
        return (
            <Panel header={(<label><Message msgId="vectorstyler.symboltitle"/></label>)} eventKey="1">
           {this.renderStyle()}
       </Panel>);
    },
    renderLabelStyler() {
        return (<Panel header={(<label><Message msgId="vectorstyler.labeltitle"/></label>)} eventKey="2">
                <Grid fluid>
                     <Row>
                            <Col xs={1}>
                                <input aria-label="..." type="checkbox" defaultChecked={false} />
                            </Col>
                            <Col style={{paddingLeft: 0, paddingTop: 1}} xs={4}>
                                <label>Label Features</label>
                            </Col>
                        </Row>
                </Grid>
                </Panel>);
    },
    renderAvancedRule() {
        return (<Panel header={(<label><Message msgId="vectorstyler.conditiontitle"/></label>)} eventKey="3">
                <Grid fluid>
                        <ScaleDenominator minValue={this.props.rule.minDenominator} maxValue={this.props.rule.maxDenominator} onChange={this.props.setRuleParameter}/>
                </Grid>
                </Panel>);
    },
    renderSelector() {
        return (<Row style={{marginBottom: "22px"}}>
                    <Row>
                        {!this.props.hideLayerSelector ? (<Col sm={4} >
                        <label><Message msgId="vectorstyler.layerlabel"/></label>
                            <Combobox data={this.props.layers.reverse()}
                                value={(this.props.layer) ? this.props.layer.id : null}
                                onChange={(value)=> this.props.selectLayer(value)}
                                valueField={"id"}
                                textField={"title"} />
                        </Col>) : null}
                        {this.props.layer ? (<Col sm={4}>
                            <label><Message msgId="vectorstyler.rulelabel"/></label>
                         <Combobox data={this.props.rules}
                                value={this.props.rule}
                                onChange={(value)=> this.props.selectRule(value.id)}
                                valueField={"id"}
                                textField={"name"} /> </Col>) : null}
                        {this.props.rule ? (
                            <Col sm={4}>
                            <label><Message msgId="vectorstyler.namelabel"/></label>
                            <FormControl type="text" onChange={(ev) => this.props.setRuleParameter('name', ev.target.value)} value={this.props.rule.name}/>
                            </Col>) : null}
                    </Row>
                </Row>);
    },
    renderVectorStyler() {
        return this.props.layer ? (
            <Row>
            <PanelGroup defaultActiveKey="1" accordion>
                    {(this.props.rule) ? this.renderSymbolStyler() : null}
                    {(this.props.rule) ? this.renderAvancedRule() : null}
            </PanelGroup>
            </Row>) : null;
    },
    renderApplyBtn() {
        let disabled = (!this.props.rule);
        return (
            <Row>
            <Col sm={3} style={{padding: 0}}><Button onClick={this.props.addRule}>
            <Glyphicon glyph="plus" /><Message msgId="vectorstyler.addrulebtn"/></Button></Col>
            <Col sm={3} style={{padding: 0}}>
            <Button disabled={disabled}
            onClick={() => this.props.removeRule(this.props.rule.id)}>
            <Glyphicon glyph="minus" /><Message msgId="vectorstyler.removerulebtn"/></Button></Col>
            <Col sm={4} smOffset={2} style={{padding: 0}}>
            <Button style={{"float": "right"}} onClick={this.apply}
            disabled={disabled} ><Message msgId="vectorstyler.applybtn"/></Button>
            </Col>
            </Row>);
    },
    renderBody() {

        return (<Grid fluid>
                {this.renderError()}
                {this.renderSelector()}
                {this.renderVectorStyler()}
                {this.props.layer ? this.renderApplyBtn() : null}
                </Grid>);
    },
    render() {
        if (this.props.forceOpen || this.props.open) {
            return this.props.withContainer ?
                (<Panel className="mapstore-vectorstyler-panel"
                        style={this.getPanelStyle()}
                        header={<label><Message msgId="vectorstyler.paneltitle"/></label>}>
                        {this.renderBody()}
                </Panel>) : this.renderBody();
        }
        return null;
    },
    apply() {
        let style = vecStyleToSLD({rules: this.props.rules, layer: this.props.layer});
        this.props.changeLayerProperties(this.props.layer.id, { params: assign({}, this.props.layer.params, {SLD_BODY: style})});
    }
});
const selector = createSelector([
    (state) => (state.controls.toolbar && state.controls.toolbar.active === 'vectorstyler'),
    ruleselctor,
    (state) => state.vectorstyler && state.vectorstyler.rules,
    (state) => state.vectorstyler && state.vectorstyler.layer,
    layersSelector
], (open, rule, rules, layer, layers) => ({
    open,
    rule,
    rules,
    layer,
    layers: layers.filter((l) => { return l.group !== 'background'; })
}));

const VectorStylerPlugin = connect(selector, {
        setVectorStyleParameter: setVectorStyleParameter,
        selectLayer: setVectorLayer,
        addRule: newVectorRule,
        removeRule: removeVectorRule,
        selectRule: selectVectorRule,
        changeLayerProperties: changeLayerProperties,
        setRuleParameter: setVectorRuleParameter
    })(VectorStyler);

module.exports = {
    VectorStylerPlugin: assign( VectorStylerPlugin,
        {
        Toolbar: {
            name: 'vectorstyler',
            help: <Message msgId="helptexts.vectorstyler"/>,
            tooltip: "vectorstyler.tooltip",
            icon: <Glyphicon glyph="pencil"/>,
            position: 9,
            panel: true,
            exclusive: true
        }
    }),
    reducers: {
        vectorstyler: require('../reducers/vectorstyler')
    }
};
