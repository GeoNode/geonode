/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const {dataContainerSelector, sliderChartSelector/*, mapSliderSelector*/, additionalChartSelector} = require('../selectors/disaster');

const {getAnalysisData, getData, setDimIdx, chartSliderUpdate/*, getSFurtherResourceData*/, setAdditionalChartIndex, toggleSwitchChart} = require('../actions/disaster');
const SliderChart = connect(sliderChartSelector, {setDimIdx, chartSliderUpdate})(require('../components/SliderChart'));
const GetCostsBtn = connect(({disaster}) => ({loading: disaster.loading || false}))(require('../components/LoadingBtn'));
const DownloadData = require('../components/DownloadData');
const MenuScenario = require('../components/MenuScenario');
const MoreInfo = require('../components/MoreInfo');
const SwitchChartBtn = connect(() => { return {}; }, { onToggle: toggleSwitchChart })(require('../components/SwitchChartBtn'));
const Overview = connect(({disaster = {}}) => ({riskItems: disaster.overview || [] }) )(require('../components/Overview'));
const {Panel, Tooltip, OverlayTrigger} = require('react-bootstrap');
// const {show, hide} = require('react-notification-system-redux');
// const ExtendedSlider = connect(mapSliderSelector, {setDimIdx, chartSliderUpdate, show, hide, getData: getSFurtherResourceData})(require('../components/ExtendedSlider'));
const AdditionalChart = connect(additionalChartSelector, {setIndex: setAdditionalChartIndex})(require('../components/AdditionalChart'));
const {generateReport} = require('../actions/report');
const DownloadBtn = connect(({disaster, report}) => {
    return {
        active: disaster.riskAnalysis && disaster.riskAnalysis.riskAnalysisData && true || false,
        downloading: report.processing
    };
}, {downloadAction: generateReport})(require('../components/DownloadBtn'));

const DataContainer = React.createClass({
    propTypes: {
        getData: React.PropTypes.func,
        getAnalysis: React.PropTypes.func,
        setDimIdx: React.PropTypes.func,
        showHazard: React.PropTypes.bool,
        className: React.PropTypes.string,
        hazardTitle: React.PropTypes.string,
        analysisType: React.PropTypes.object,
        riskAnalysisData: React.PropTypes.object,
        dim: React.PropTypes.object,
        showChart: React.PropTypes.bool,
        hazardType: React.PropTypes.shape({
            mnemonic: React.PropTypes.string,
            description: React.PropTypes.string,
            analysisTypes: React.PropTypes.arrayOf(React.PropTypes.shape({
                name: React.PropTypes.string,
                title: React.PropTypes.string,
                href: React.PropTypes.string
                }))
        })
    },
    getDefaultProps() {
        return {
            showHazard: false,
            getData: () => {},
            getAnalysis: () => {},
            className: "col-sm-7"
        };
    },
    getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++ ) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    },
    getChartData(data, val) {
        const {dim} = this.props;
        const nameIdx = dim === 0 ? 1 : 0;
        return data.filter((d) => d[nameIdx] === val ).map((v) => {return {"name": v[dim], "value": parseInt(v[2], 10)}; });
    },
    renderAnalysisData() {
        const {hazardSet, data} = this.props.riskAnalysisData;
        const tooltip = (<Tooltip id={"tooltip-back"} className="disaster">{'Back to Analysis Table'}</Tooltip>);
        return (
            <div id="disaster-analysis-data-container" className="container-fluid">
                <div className="row">
                    <div className="btn-group">
                        <OverlayTrigger placement="bottom" overlay={tooltip}>
                            <button id="disaster-back-button" onClick={()=> this.props.getData(this.props.analysisType.href, true)} className="btn btn-primary">
                                <i className="fa fa-arrow-left"/>
                            </button>
                        </OverlayTrigger>
                        <MoreInfo/>
                        <SwitchChartBtn/>
                    </div>
                    <div className="btn-group pull-right">
                        <DownloadBtn/>
                        <DownloadData/>
                    </div>
                </div>
                <div className="row">
                    <h4 style={{margin: 0}}>{hazardSet.title}</h4>
                </div>
                <div className="row">
                    <p dangerouslySetInnerHTML={{__html: hazardSet.purpose}}/>
                </div>
                <div className="row">
                    <MenuScenario dim={this.props.dim} dimensions={data.dimensions} setDimIdx={this.props.setDimIdx}/>
                </div>
                <div id="disaster-chart-container" className="row">
                    {!this.props.showChart ? <AdditionalChart dim={this.props.dim} /> : <div><SliderChart uid={'map_slider'}/>{/*<ExtendedSlider uid={'chart_label_tab'} dimIdx={'dim1Idx'}/>*/}</div>}
                </div>
            </div>
        );
    },
    renderRiskAnalysisHeader(title, getAnalysis, rs, idx) {
        const tooltip = (<Tooltip id={"tooltip-abstract-" + idx} className="disaster">{'Show Abstract'}</Tooltip>);
        return (
          <OverlayTrigger placement="top" overlay={tooltip}>
          <div className="row">
            <div className="col-xs-10">
              <div className="disaster-analysis-title">{title}</div>
            </div>
            <div className="col-xs-2">
                <i className="pull-right fa fa-chevron-down"></i>
            </div>
          </div>
          </OverlayTrigger>
        );
    },
    renderRiskAnalysis() {
        const {analysisType = {}, getAnalysis} = this.props;
        return analysisType.riskAnalysis.map((rs, idx) => {
            const {title, fa_icon: faIcon, abstract} = rs.hazardSet;
            const tooltip = (<Tooltip id={"tooltip-icon-cat-" + idx} className="disaster">{'Analysis Data'}</Tooltip>);
            return (
              <div key={idx} className="row">
                  <div className="col-xs-1 text-center">
                      <OverlayTrigger placement="bottom" overlay={tooltip}>
                        <i className={'disaster-category fa ' + faIcon} onClick={()=> getAnalysis(rs.href)}></i>
                      </OverlayTrigger>
                  </div>
                  <div className="col-xs-11">
                    <Panel collapsible header={this.renderRiskAnalysisHeader(title, getAnalysis, rs, idx)}>
                        {abstract}
                        <br/>
                        <GetCostsBtn onClick={()=> getAnalysis(rs.href)}
                        iconClass="fa fa-bar-chart" label="Analysis Data"/>
                    </Panel>
                  </div>
              </div>
            );
        });
    },
    renderAnalysisTab() {
        const {hazardType = {}, analysisType = {}, getData: loadData} = this.props;
        return (hazardType.analysisTypes || []).map((type, idx) => {
            const {href, name, title, faIcon, description} = type;
            const active = name === analysisType.name;
            const tooltip = (<Tooltip id={"tooltip-icon-analysis-tab-" + idx} className="disaster">{description}</Tooltip>);
            return (
                <OverlayTrigger key={name} placement="bottom" overlay={tooltip}>
                    <li className={`text-center ${active ? 'active' : ''}`} onClick={() => loadData(href, true)}>
                        <a href="#" data-toggle="tab"><span> <i className={"fa fa-" + faIcon}></i>&nbsp;{title}</span></a>
                    </li>
                </OverlayTrigger>
            );
        });
    },
    renderHazard() {
        const {riskAnalysisData} = this.props;

        return (<div className={this.props.className}>
                <div className="disaster-header">
                  {riskAnalysisData.name ? (
                    <div className="container-fluid">
                        {this.renderAnalysisData()}
                    </div>
                    ) : (
                    <div className="container-fluid">
                        <ul id="disaster-analysis-menu" className="nav nav-pills">
                            {this.renderAnalysisTab()}
                        </ul>
                        <hr></hr>
                        <div id="disaster-analysis-container" className="disaster-analysis">
                            <div className="container-fluid">
                                {this.renderRiskAnalysis()}
                            </div>
                        </div>
                    </div>
                  )}
                </div>
            </div>
        );
    },
    render() {
        const {showHazard, getData: loadData} = this.props;
        return showHazard ? this.renderHazard() : (<Overview className={this.props.className} getData={loadData}/>);
    }
});

module.exports = connect(dataContainerSelector, {getAnalysis: getAnalysisData, getData, setDimIdx})(DataContainer);
