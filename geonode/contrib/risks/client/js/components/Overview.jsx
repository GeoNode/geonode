/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const Overview = React.createClass({
    propTypes: {
        riskItems: React.PropTypes.arrayOf(React.PropTypes.shape({
            title: React.PropTypes.string.isRequired,
            mnemonic: React.PropTypes.string.isRequired,
            herf: React.PropTypes.string,
            riskAnalysis: React.PropTypes.number
        })),
        className: React.PropTypes.string,
        getData: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            className: "col-sm-7",
            getData: () => {}
        };
    },
    getItems() {
        const {riskItems, getData} = this.props;
        return riskItems.map((item, idx) => {
            const {title, mnemonic, href, riskAnalysis} = item;
            const noData = !(riskAnalysis > 0);
            const count = <span>{'Overall Risk Analysis Available '}<span className="level-count">{riskAnalysis}</span></span>;
            return (
            <div key={idx} className={`${noData ? 'level-no-data' : 'level-data'} overview container-fluid`} onClick={noData ? undefined : () => getData(href, true)}>
                <div className="row">
                      <div className="col-xs-6"><i className={`icon-${mnemonic.toLowerCase()}`}/>&nbsp;{title}</div>
                      <div className="col-xs-6 text-right"><span className="level">{riskAnalysis ? count : 'No Data Available'}</span></div>
                </div>
            </div>);
        });
    },
    render() {
        return (
            <div id="disaster-overview-list" style={{minHeight: 500}} className={this.props.className + ' disaster-level-container'}>
                <aside className="disaster-level">Analysis</aside>
                {this.getItems()}
            </div>);
    }
});

module.exports = Overview;
