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
const {downloadDataSelector} = require('../selectors/disaster');

const DownloadData = React.createClass({
    propTypes: {
        uid: React.PropTypes.string,
        riskAnalysisData: React.PropTypes.object,
        show: React.PropTypes.func,
        hide: React.PropTypes.func,
        download: React.PropTypes.array
    },
    getDefaultProps() {
        return {
            uid: 'download_tab',
            riskAnalysisData: {},
            show: () => {},
            hide: () => {},
            download: [],
            moreInfo: []
        };
    },
    render() {
        const active = this.props.download.length > 0 ? ' active' : '';
        const {uid} = this.props;
        const {dataFile, metadataFile} = this.props.riskAnalysisData;
        const downloadFile = dataFile || metadataFile ? (
            <div>
                <h4 className="text-center"><i className="fa fa-download"/>&nbsp;{'Download'}</h4>
                <ul className="nav nav-pills nav-stacked">
                    <li className="text-center"><a href={`${dataFile}`} download>{'Data'}</a></li>
                    <li className="text-center"><a href={`${metadataFile}`} download>{'Metadata'}</a></li>
                </ul>
            </div>
        ) : ( <h4 className="text-center">{'No files available'}</h4>);
        return (
            <button id="disaster-download-data-button" className={"btn btn-primary" + active} onClick={() => { return this.props.download.length === 0 ? this.props.show({uid, position: 'bc', autoDismiss: 0, children: downloadFile}, 'info') : this.props.hide(uid); }}>
                <i className="fa fa-download"/>
            </button>
        );
    }
});

module.exports = connect(downloadDataSelector, { show, hide })(DownloadData);
