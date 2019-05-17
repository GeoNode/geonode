/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ReactDOM = require('react-dom');

const ZoneField = require('../ZoneField.jsx');
const {featureCollection} = require('../../../../test-resources/featureCollectionZone.js');

const expect = require('expect');

describe('ZoneField', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the ZoneField component', () => {
        const zone = {
            id: 1,
            url: null,
            typeName: "geosolutions:zones",
            values: featureCollection.features,
            value: null,
            valueField: "properties.ITD_Dist_n",
            textField: "properties.DistNum",
            searchText: "*",
            searchMethod: "ilike",
            searchAttribute: "DistNum",
            label: "ITD District"
        };

        const zoneField = ReactDOM.render(
            <ZoneField
                key={zone.id}
                open={zone.open || false}
                zoneId={zone.id}
                url={zone.url}
                typeName={zone.typeName}
                wfs={zone.wfs}
                busy={zone.busy || false}
                label={zone.label}
                values={zone.values}
                value={zone.value}
                valueField= {zone.valueField}
                textField= {zone.textField}
                searchText={zone.searchText}
                searchMethod={zone.searchMethod}
                searchAttribute={zone.searchAttribute}
                disabled={zone.disabled || false}
                dependsOn={zone.dependson}/>,
            document.getElementById("container")
        );

        expect(zoneField).toExist();

        expect(zoneField.props.values).toExist();
        expect(zoneField.props.values.length).toBe(6);
        expect(zoneField.props.typeName).toBe("geosolutions:zones");
        expect(zoneField.props.busy).toBe(false);
        expect(zoneField.props.open).toBe(false);
        expect(zoneField.props.disabled).toBe(false);

        const zoneFieldDOMNode = expect(ReactDOM.findDOMNode(zoneField));
        expect(zoneFieldDOMNode).toExist();
    });
});
