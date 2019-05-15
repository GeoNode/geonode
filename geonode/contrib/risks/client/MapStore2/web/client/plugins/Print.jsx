/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');

const LocaleUtils = require('../utils/LocaleUtils');
const CoordinatesUtils = require('../utils/CoordinatesUtils');
const MapUtils = require('../utils/MapUtils');
const Dialog = require('../components/misc/Dialog');

const {Grid, Row, Col, Panel, Accordion, Glyphicon} = require('react-bootstrap');

const {toggleControl, setControlProperty} = require('../actions/controls');
const {printSubmit, printSubmitting, configurePrintMap} = require('../actions/print');

const {mapSelector} = require('../selectors/map');
const {layersSelector} = require('../selectors/layers');

const {createSelector} = require('reselect');

const assign = require('object-assign');

const {head} = require('lodash');

const {scalesSelector} = require('../selectors/map');

require('./print/print.css');

const {
    Name,
    Description,
    Resolution,
    DefaultBackgroundOption,
    Sheet,
    LegendOption,
    MultiPageOption,
    LandscapeOption,
    ForceLabelsOption,
    AntiAliasingOption,
    IconSizeOption,
    LegendDpiOption,
    Font,
    MapPreview,
    PrintSubmit,
    PrintPreview
} = require('./print/index');

const PrintUtils = require('../utils/PrintUtils');
const Message = require('../components/I18N/Message');

const Print = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        layers: React.PropTypes.array,
        capabilities: React.PropTypes.object,
        printSpec: React.PropTypes.object,
        printSpecTemplate: React.PropTypes.object,
        withContainer: React.PropTypes.bool,
        withPanelAsContainer: React.PropTypes.bool,
        open: React.PropTypes.bool,
        pdfUrl: React.PropTypes.string,
        title: React.PropTypes.string,
        style: React.PropTypes.object,
        mapWidth: React.PropTypes.number,
        mapType: React.PropTypes.string,
        alternatives: React.PropTypes.array,
        toggleControl: React.PropTypes.func,
        onBeforePrint: React.PropTypes.func,
        setPage: React.PropTypes.func,
        onPrint: React.PropTypes.func,
        configurePrintMap: React.PropTypes.func,
        getPrintSpecification: React.PropTypes.func,
        getLayoutName: React.PropTypes.func,
        error: React.PropTypes.string,
        getZoomForExtent: React.PropTypes.func,
        minZoom: React.PropTypes.number,
        maxZoom: React.PropTypes.number,
        usePreview: React.PropTypes.bool,
        mapPreviewOptions: React.PropTypes.object,
        syncMapPreview: React.PropTypes.bool,
        useFixedScales: React.PropTypes.bool,
        scales: React.PropTypes.array,
        ignoreLayers: React.PropTypes.array,
        defaultBackground: React.PropTypes.string,
        closeGlyph: React.PropTypes.string,
        submitConfig: React.PropTypes.object,
        previewOptions: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {

        return {
            withContainer: true,
            withPanelAsContainer: false,
            title: 'print.paneltitle',
            toggleControl: () => {},
            onBeforePrint: () => {},
            setPage: () => {},
            onPrint: () => {},
            configurePrintMap: () => {},
            printSpecTemplate: {},
            getPrintSpecification: PrintUtils.getMapfishPrintSpecification,
            getLayoutName: PrintUtils.getLayoutName,
            getZoomForExtent: MapUtils.defaultGetZoomForExtent,
            pdfUrl: null,
            mapWidth: 370,
            mapType: "leaflet",
            minZoom: 1,
            maxZoom: 23,
            alternatives: [{
                name: "legend",
                component: LegendOption,
                regex: /legend/
            }, {
                name: "2pages",
                component: MultiPageOption,
                regex: /2_pages/
            }, {
                name: "landscape",
                component: LandscapeOption,
                regex: /landscape/
            }],
            usePreview: true,
            mapPreviewOptions: {
                enableScalebox: false,
                enableRefresh: false
            },
            syncMapPreview: true,
            useFixedScales: false,
            scales: [],
            ignoreLayers: ["google", "bing"],
            defaultBackground: "osm",
            closeGlyph: "1-close",
            submitConfig: {
                buttonConfig: {
                  bsSize: "small",
                  bsStyle: "primary"
                },
                glyph: ""
            },
            previewOptions: {
                buttonStyle: "primary"
            },
            style: {}
        };
    },
    componentWillMount() {
        if (this.props.usePreview && !window.PDFJS) {
            const s = document.createElement("script");
            s.type = "text/javascript";
            s.src = "https://unpkg.com/pdfjs-dist@1.4.79/build/pdf.combined.js";
            document.head.appendChild(s);
        }
        this.configurePrintMap();
    },
    componentWillReceiveProps(nextProps) {
        const hasBeenOpened = nextProps.open && !this.props.open;
        const mapHasChanged = this.props.open && this.props.syncMapPreview && MapUtils.mapUpdated(this.props.map, nextProps.map);
        const specHasChanged = nextProps.printSpec.defaultBackground !== this.props.printSpec.defaultBackground;
        if (hasBeenOpened || mapHasChanged || specHasChanged) {
            this.configurePrintMap(nextProps.map, nextProps.printSpec);
        }
    },
    getMapSize(layout) {
        const currentLayout = layout || this.getLayout();
        return {
            width: this.props.mapWidth,
            height: currentLayout && currentLayout.map.height / currentLayout.map.width * this.props.mapWidth || 270
        };
    },
    getLayout() {
        const layoutName = this.props.getLayoutName(this.props.printSpec);
        return head(this.props.capabilities.layouts.filter((l) => l.name === layoutName));
    },
    renderLayoutsAlternatives() {
        return this.props.alternatives.map((alternative) => (
            <alternative.component key={"printoption_" + alternative.name}
                label={LocaleUtils.getMessageById(this.context.messages, "print.alternatives." + alternative.name)}
                enableRegex={alternative.regex}
            />
        ));
    },
    renderPreviewPanel() {
        return <PrintPreview {...this.props.previewOptions} role="body" prevPage={this.prevPage} nextPage={this.nextPage}/>;
    },
    renderError() {
        if (this.props.error) {
            return <Row><Col xs={12}><div className="print-error"><span>{this.props.error}</span></div></Col></Row>;
        }
        return null;
    },
    renderWarning(layout) {
        if (!layout) {
            return <Row><Col xs={12}><div className="print-warning"><span><Message msgId="print.layoutWarning"/></span></div></Col></Row>;
        }
        return null;
    },
    renderPrintPanel() {
        const layout = this.getLayout();
        const layoutName = this.props.getLayoutName(this.props.printSpec);
        const mapSize = this.getMapSize(layout);
        return (
            <Grid fluid role="body">
            {this.renderError()}
            {this.renderWarning(layout)}
            <Row>
                <Col xs={12} md={6}>
                    <Name label={LocaleUtils.getMessageById(this.context.messages, 'print.title')} placeholder={LocaleUtils.getMessageById(this.context.messages, 'print.titleplaceholder')} />
                    <Description label={LocaleUtils.getMessageById(this.context.messages, 'print.description')} placeholder={LocaleUtils.getMessageById(this.context.messages, 'print.descriptionplaceholder')} />
                    <Accordion defaultActiveKey="1">
                        <Panel className="print-layout" header={LocaleUtils.getMessageById(this.context.messages, "print.layout")} eventKey="1" collapsible>
                            <Sheet key="sheetsize"
                                layouts={this.props.capabilities.layouts}
                                label={LocaleUtils.getMessageById(this.context.messages, "print.sheetsize")}
                                />
                            {this.renderLayoutsAlternatives()}
                        </Panel>
                        <Panel className="print-legend-options" header={LocaleUtils.getMessageById(this.context.messages, "print.legendoptions")} eventKey="2" collapsible>
                            <Font label={LocaleUtils.getMessageById(this.context.messages, "print.legend.font")}/>
                            <ForceLabelsOption label={LocaleUtils.getMessageById(this.context.messages, "print.legend.forceLabels")}/>
                            <AntiAliasingOption label={LocaleUtils.getMessageById(this.context.messages, "print.legend.antiAliasing")}/>
                            <IconSizeOption label={LocaleUtils.getMessageById(this.context.messages, "print.legend.iconsSize")}/>
                            <LegendDpiOption label={LocaleUtils.getMessageById(this.context.messages, "print.legend.dpi")}/>
                        </Panel>
                    </Accordion>
                </Col>
                <Col xs={12} md={6} style={{textAlign: "center"}}>
                    <Resolution label={LocaleUtils.getMessageById(this.context.messages, "print.resolution")}/>
                    <MapPreview width={mapSize.width} height={mapSize.height} mapType={this.props.mapType}
                        onMapRefresh={() => this.configurePrintMap()}
                        layout={layoutName}
                        layoutSize={layout && layout.map || {width: 10, height: 10}}
                        resolutions={this.props.useFixedScales ? null : MapUtils.getResolutions()}
                        {...this.props.mapPreviewOptions}
                        />
                    {this.isBackgroundIgnored() ? <DefaultBackgroundOption label={LocaleUtils.getMessageById(this.context.messages, "print.defaultBackground")}/> : null}
                    <PrintSubmit {...this.props.submitConfig} disabled={!layout} onPrint={this.print}/>
                    {this.renderDownload()}
                </Col>
            </Row>
        </Grid>
        );
    },
    renderDownload() {
        if (this.props.pdfUrl && !this.props.usePreview) {
            return <iframe src={this.props.pdfUrl} style={{visibility: "hidden", display: "none"}}/>;
        }
        return null;
    },
    renderBody() {
        if (this.props.pdfUrl && this.props.usePreview) {
            return this.renderPreviewPanel();
        }
        return this.renderPrintPanel();
    },
    render() {
        if ((this.props.capabilities || this.props.error) && this.props.open) {
            if (this.props.withContainer) {
                if (this.props.withPanelAsContainer) {
                    return (<Panel className="mapstore-print-panel" header={<span><span className="print-panel-title"><Message msgId="print.paneltitle"/></span><span className="print-panel-close panel-close" onClick={this.props.toggleControl}></span></span>} style={this.props.style}>
                        {this.renderBody()}
                    </Panel>);
                }
                return (<Dialog id="mapstore-print-panel" style={this.props.style}>
                    <span role="header"><span className="print-panel-title"><Message msgId="print.paneltitle"/></span><button onClick={this.props.toggleControl} className="print-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button></span>
                    {this.renderBody()}
                </Dialog>);
            }
            return this.renderBody();
        }
        return null;
    },
    isAllowed(layer) {
        return this.props.ignoreLayers.indexOf(layer.type) === -1;
    },
    isBackgroundIgnored() {
        return this.props.layers.filter((layer) => layer.visibility && !this.isAllowed(layer)).length > 0;
    },
    filterLayers(printSpec) {
        const filtered = this.props.layers.filter((layer) => layer.visibility && this.isAllowed(layer));
        if (this.isBackgroundIgnored() && this.props.defaultBackground && printSpec.defaultBackground) {
            const defaultBackground = this.props.layers.filter((layer) => layer.type === this.props.defaultBackground)[0];
            return [assign({}, defaultBackground, {visibility: true}), ...filtered];
        }
        return filtered;
    },
    configurePrintMap(map, printSpec) {
        const newMap = map || this.props.map;
        const newPrintSpec = printSpec || this.props.printSpec;
        if (newMap && newMap.bbox && this.props.capabilities) {
            const bbox = CoordinatesUtils.reprojectBbox([
                newMap.bbox.bounds.minx,
                newMap.bbox.bounds.miny,
                newMap.bbox.bounds.maxx,
                newMap.bbox.bounds.maxy
            ], newMap.bbox.crs, newMap.projection);
            const mapSize = this.getMapSize();
            if (this.props.useFixedScales) {
                const mapZoom = this.props.getZoomForExtent(bbox, mapSize, this.props.minZoom, this.props.maxZoom);
                const scales = PrintUtils.getPrintScales(this.props.capabilities);
                const scaleZoom = PrintUtils.getNearestZoom(newMap.zoom, scales);

                this.props.configurePrintMap(newMap.center, mapZoom, scaleZoom, scales[scaleZoom],
                    this.filterLayers(newPrintSpec), newMap.projection);
            } else {
                this.props.configurePrintMap(newMap.center, newMap.zoom, newMap.zoom, this.props.scales[newMap.zoom],
                    this.filterLayers(newPrintSpec), newMap.projection);
            }
        }
    },
    print() {
        const spec = this.props.getPrintSpecification(this.props.printSpec);
        this.props.setPage(0);
        this.props.onBeforePrint();
        this.props.onPrint(this.props.capabilities.createURL, spec);
    }
});

const selector = createSelector([
    (state) => (state.controls.print && state.controls.print.enabled ) || (state.controls.toolbar && state.controls.toolbar.active === 'print'),
    (state) => state.print && state.print.capabilities,
    (state) => state.print && state.print.spec && assign({}, state.print.spec, state.print.map || {}),
    (state) => state.print && state.print.pdfUrl,
    (state) => state.print && state.print.error,
    mapSelector,
    layersSelector,
    scalesSelector,
    (state) => state.browser && (!state.browser.ie || state.browser.ie11)
], (open, capabilities, printSpec, pdfUrl, error, map, layers, scales, usePreview) => ({
    open,
    capabilities,
    printSpec,
    pdfUrl,
    error,
    map,
    layers,
    scales,
    usePreview
}));

const PrintPlugin = connect(selector, {
    toggleControl: toggleControl.bind(null, 'print', null),
    onPrint: printSubmit,
    onBeforePrint: printSubmitting,
    setPage: setControlProperty.bind(null, 'print', 'currentPage'),
    configurePrintMap
})(Print);

module.exports = {
    PrintPlugin: assign(PrintPlugin, {
        Toolbar: {
            name: 'print',
            position: 7,
            help: <Message msgId="helptexts.print"/>,
            tooltip: "printbutton",
            icon: <Glyphicon glyph="print"/>,
            exclusive: true,
            panel: true,
            priority: 1
        },
        BurgerMenu: {
            name: 'print',
            position: 2,
            text: <Message msgId="printbutton"/>,
            icon: <Glyphicon glyph="print"/>,
            action: toggleControl.bind(null, 'print', null),
            priority: 2,
            doNotHide: true
        }
    }),
    reducers: {print: require('../reducers/print')}
};
