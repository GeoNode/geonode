/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const Debug = require('../../../components/development/Debug');
const Localized = require('../../../components/I18N/Localized');
const {connect} = require('react-redux');
const agGrid = require('ag-grid');
const FeatureGridMap = require('../components/FeatureGridMap');
const FeatureGridComp = require('../components/SmartFeatureGrid');

const FeatureGrid = (props) => (
    <Localized messages={props.messages} locale={props.locale}>
        <div>
            <FeatureGridMap/>
            <FeatureGridComp style={{
                        width: "30%",
                        position: "absolute",
                        top: "10px",
                        left: "40px",
                        zIndex: 100}}
                        title="Basic Grid"/>
            <FeatureGridComp enableZoomToFeature={false} style={{
                        width: "30%",
                        position: "absolute",
                        top: "60px",
                        left: "40px",
                        zIndex: 99}}
                        title="Table With Groups"
                        columnDefs={[
                            {headerName: "NAME", width: 150, field: "properties.STATE_NAME", comparator: agGrid.defaultGroupComparator,
                            cellRenderer: {renderer: 'group'}},
                            {headerName: "POPULATION", width: 100, field: "properties.PERSONS"},
                            {headerName: "REGION", width: 100, field: "properties.SUB_REGION", rowGroupIndex: 0}
                            ]}
                        agGridOptions={{
                            groupSuppressAutoColumn: true,
                            groupUseEntireRow: false,
                            groupAggFunction: function(nodes) {
                                var sum = 0;
                                nodes.forEach(function(node) {
                                    var data = node.data;
                                    sum += data.properties.PERSONS;
                                });
                                return {properties: {PERSONS: sum}};
                            }
                    }}/>
            <Debug/>
        </div>
    </Localized>
);

FeatureGrid.propTypes = {
    messages: React.PropTypes.object,
    locale: React.PropTypes.string
};

module.exports = connect((state) => {
    return {
        locale: state.locale && state.locale.current,
        messages: state.locale && state.locale.messages || {}
    };
})(FeatureGrid);
