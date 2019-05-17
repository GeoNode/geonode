/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const {getData, zoomInOut} = require('../actions/disaster');
const {topBarSelector} = require('../selectors/disaster');
const {toggleControl} = require('../../MapStore2/web/client/actions/controls');
const Notifications = connect(state => ({notifications: state.notifications}))(require('react-notification-system-redux'));
const TopBar = connect(topBarSelector, {zoom: zoomInOut, getData, toggleTutorial: toggleControl.bind(null, 'tutorial', null)})(require('../components/TopBar'));
const CostDataContainer = require('../containers/CostDataContainer');
const CostsMapContainer = require('../containers/CostsMapContainer');
const Page = require('../../MapStore2/web/client/containers/Page');
const ConfigUtils = require('../../MapStore2/web/client/utils/ConfigUtils');
const NotificationStyle = require('../../assets/js/NotificationStyle');
const ReportMap = require('../components/ReportMapImage');

const Home = React.createClass({
    propTypes: {
        params: React.PropTypes.object,
        locale: React.PropTypes.string,
        messages: React.PropTypes.object,
        plugins: React.PropTypes.object,
        reportprocessing: React.PropTypes.bool,
        generateMap: React.PropTypes.bool
    },
    render() {
        const {plugins} = this.props;
        let pluginsHome = ConfigUtils.getConfigProp("plugins") || {};
        let pagePlugins = {
            "desktop": pluginsHome.common || [],
            "mobile": pluginsHome.common || []
        };
        let pluginsConfig = {
            "desktop": pluginsHome.home || [],
            "mobile": pluginsHome.home || []
        };
        return (
            <div className="disaster">
                <Notifications style={NotificationStyle}/>
                    <Page
                      id="home"
                      pagePluginsConfig={pagePlugins}
                      pluginsConfig={pluginsConfig}
                      plugins={plugins}
                      params={this.props.params}
                      />
                    <TopBar/>
                    <div className="container-fluid">
                        <div className="row">
                            <CostDataContainer/>
                            {<CostsMapContainer plugins={plugins}/>}
                        </div>
                    </div>
                   {this.props.generateMap ? (<ReportMap/>) : null}
                   {this.props.generateMap ? (<div className="freeze-app" />) : null}
                </div>
        );
    }
});

module.exports = connect((state) => {
    return {
        error: state.loadingError || (state.locale && state.locale.localeError) || null,
        locale: state.locale && state.locale.current,
        messages: state.locale && state.locale.messages || {},
        reportprocessing: state.report && state.report.processing,
        generateMap: state.report && state.report.generateMap
    };
})(Home);
