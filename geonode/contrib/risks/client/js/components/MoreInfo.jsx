/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {show, hide} = require('react-notification-system-redux');
const {moreInfoSelector} = require('../selectors/disaster');
const {isObject} = require('lodash');

const MoreInfo = React.createClass({
    propTypes: {
        uid: React.PropTypes.string,
        riskAnalysisData: React.PropTypes.object,
        show: React.PropTypes.func,
        hide: React.PropTypes.func,
        moreInfo: React.PropTypes.array
    },
    getDefaultProps() {
        return {
            uid: 'more_info_tab',
            riskAnalysisData: {},
            show: () => {},
            hide: () => {},
            moreInfo: []
        };
    },
    getDataAttributes(data) {
        const attributes = Object.keys(data);
        attributes.sort();
        return attributes.map((item, idx) => {
            let obj = data[item];
            return obj !== "" && obj !== null ? (
              <div key={idx}>
                  <div className="disaster-more-info-even">{item}</div>
                  {isObject(obj) ? (<div className="disaster-more-info-table-nested">{this.getDataAttributes(obj)}</div>) : (<div className="disaster-more-info-odd">{obj}</div>)}
              </div>
          ) : null;
        });
    },
    render() {
        const active = this.props.moreInfo.length > 0 ? ' active' : '';
        const {uid} = this.props;
        const {hazardSet} = this.props.riskAnalysisData;
        const moreInfoTab = (
            <div className="disaster-more-info-table-notification">
                <h4 className="text-center"><i className="fa fa-ellipsis-h"/>&nbsp;{'More info'}</h4>
                <div className="disaster-more-info-table-container">
                    <div className="disaster-more-info-table">
                        {this.getDataAttributes(hazardSet)}
                    </div>
                </div>
            </div>
        );
        return (
            <button id="disaster-more-info-button" className={"btn btn-primary" + active} onClick={() => { return this.props.moreInfo.length === 0 ? this.props.show({uid, position: 'bc', autoDismiss: 0, children: moreInfoTab}, 'info') : this.props.hide(uid); }}>
                <i className="fa fa-ellipsis-h"/>
            </button>
        );
    }
});

module.exports = connect(moreInfoSelector, { show, hide })(MoreInfo);
