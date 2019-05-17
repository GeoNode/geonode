/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    ADD_FILTER_FIELD,
    ADD_GROUP_FIELD,
    REMOVE_FILTER_FIELD,
    UPDATE_FILTER_FIELD,
    UPDATE_EXCEPTION_FIELD,
    UPDATE_LOGIC_COMBO,
    REMOVE_GROUP_FIELD,
    CHANGE_CASCADING_VALUE,
    EXPAND_ATTRIBUTE_PANEL,
    EXPAND_SPATIAL_PANEL,
    SELECT_SPATIAL_METHOD,
    SELECT_SPATIAL_OPERATION,
    REMOVE_SPATIAL_SELECT,
    SHOW_SPATIAL_DETAILS,
    ZONE_SEARCH,
    ZONE_SEARCH_ERROR,
    ZONE_FILTER,
    // OPEN_MENU,
    ZONE_CHANGE,
    ZONES_RESET,
    SHOW_GENERATED_FILTER,
    QUERY_FORM_RESET,
    CHANGE_DWITHIN_VALUE,
    SIMPLE_FILTER_FIELD_UPDATE,
    ADD_SIMPLE_FILTER_FIELD,
    REMOVE_SIMPLE_FILTER_FIELD,
    REMOVE_ALL_SIMPLE_FILTER_FIELDS,
    changeDwithinValue,
    resetZones,
    zoneChange,
   //  openMenu,
    zoneSearch,
    zoneSearchError,
    zoneFilter,
    zoneGetValues,
    query,
    reset,
    addFilterField,
    addGroupField,
    removeFilterField,
    updateFilterField,
    updateExceptionField,
    updateLogicCombo,
    removeGroupField,
    changeCascadingValue,
    expandAttributeFilterPanel,
    expandSpatialFilterPanel,
    selectSpatialMethod,
    selectSpatialOperation,
    removeSpatialSelection,
    showSpatialSelectionDetails,
    simpleFilterFieldUpdate,
    addSimpleFilterField,
    removeSimpleFilterField,
    removeAllSimpleFilterFields
} = require('../queryform');

describe('Test correctness of the queryform actions', () => {

    it('addFilterField', () => {
        let groupId = 1;

        var retval = addFilterField(groupId);

        expect(retval).toExist();
        expect(retval.type).toBe(ADD_FILTER_FIELD);
        expect(retval.groupId).toBe(1);
    });

    it('addGroupField', () => {
        let groupId = 1;
        let index = 0;

        var retval = addGroupField(groupId, index);

        expect(retval).toExist();
        expect(retval.type).toBe(ADD_GROUP_FIELD);
        expect(retval.groupId).toBe(1);
        expect(retval.index).toBe(0);
    });

    it('removeFilterField', () => {
        let rowId = 100;

        let retval = removeFilterField(rowId);

        expect(retval).toExist();
        expect(retval.type).toBe(REMOVE_FILTER_FIELD);
        expect(retval.rowId).toBe(100);
    });

    it('updateFilterField', () => {
        let rowId = 100;
        let fieldName = "fieldName";
        let fieldValue = "fieldValue";

        let retval = updateFilterField(rowId, fieldName, fieldValue);

        expect(retval).toExist();
        expect(retval.type).toBe(UPDATE_FILTER_FIELD);
        expect(retval.rowId).toBe(100);
        expect(retval.fieldName).toBe("fieldName");
        expect(retval.fieldValue).toBe("fieldValue");
    });

    it('updateExceptionField', () => {
        let rowId = 100;
        let message = "message";

        let retval = updateExceptionField(rowId, message);

        expect(retval).toExist();
        expect(retval.type).toBe(UPDATE_EXCEPTION_FIELD);
        expect(retval.rowId).toBe(100);
        expect(retval.exceptionMessage).toBe("message");
    });

    it('updateLogicCombo', () => {
        let groupId = 100;
        let logic = "OR";

        let retval = updateLogicCombo(groupId, logic);

        expect(retval).toExist();
        expect(retval.type).toBe(UPDATE_LOGIC_COMBO);
        expect(retval.groupId).toBe(100);
        expect(retval.logic).toBe("OR");
    });

    it('removeGroupField', () => {
        let groupId = 100;

        let retval = removeGroupField(groupId);

        expect(retval).toExist();
        expect(retval.type).toBe(REMOVE_GROUP_FIELD);
        expect(retval.groupId).toBe(100);
    });

    it('changeCascadingValue', () => {
        let attributes = [];

        let retval = changeCascadingValue(attributes);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_CASCADING_VALUE);
        expect(retval.attributes.length).toBe(0);
    });

    it('expandAttributeFilterPanel', () => {
        let expanded = false;

        let retval = expandAttributeFilterPanel(expanded);

        expect(retval).toExist();
        expect(retval.type).toBe(EXPAND_ATTRIBUTE_PANEL);
        expect(retval.expand).toBe(false);
    });

    it('expandSpatialFilterPanel', () => {
        let expanded = false;

        let retval = expandSpatialFilterPanel(expanded);

        expect(retval).toExist();
        expect(retval.type).toBe(EXPAND_SPATIAL_PANEL);
        expect(retval.expand).toBe(false);
    });

    it('selectSpatialMethod', () => {
        let method = "BBOX";
        let fieldName = "method";

        let retval = selectSpatialMethod(method, fieldName);

        expect(retval).toExist();
        expect(retval.type).toBe(SELECT_SPATIAL_METHOD);
        expect(retval.method).toBe("BBOX");
        expect(retval.fieldName).toBe("method");
    });

    it('selectSpatialOperation', () => {
        let operation = "DWITHIN";
        let fieldName = "operation";

        let retval = selectSpatialOperation(operation, fieldName);

        expect(retval).toExist();
        expect(retval.type).toBe(SELECT_SPATIAL_OPERATION);
        expect(retval.operation).toBe("DWITHIN");
        expect(retval.fieldName).toBe("operation");
    });

    it('removeSpatialSelection', () => {
        let retval = removeSpatialSelection();

        expect(retval).toExist();
        expect(retval.type).toBe(REMOVE_SPATIAL_SELECT);
    });

    it('showSpatialSelectionDetails', () => {
        let show = true;

        let retval = showSpatialSelectionDetails(show);

        expect(retval).toExist();
        expect(retval.type).toBe(SHOW_SPATIAL_DETAILS);
        expect(retval.show).toBe(true);
    });

    it('changeDwithinValue', () => {
        let retval = changeDwithinValue(1);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_DWITHIN_VALUE);
        expect(retval.distance).toBe(1);
    });

    it('query', () => {
        let retval = query("url", null);

        expect(retval).toExist();
        expect(retval.type).toBe(SHOW_GENERATED_FILTER);
        expect(retval.data).toBe(null);
    });

    it('reset', () => {
        let retval = reset();

        expect(retval).toExist();
        expect(retval.type).toBe(QUERY_FORM_RESET);
    });

    it('resetZones', () => {
        let retval = resetZones();

        expect(retval).toExist();
        expect(retval.type).toBe(ZONES_RESET);
    });

    it('zoneFilter', () => {
        let retval = zoneFilter(null, 1);

        expect(retval).toExist();
        expect(retval.type).toBe(ZONE_FILTER);
        expect(retval.data).toBe(null);
        expect(retval.id).toBe(1);
    });

    it('zoneSearchError', () => {
        let retval = zoneSearchError("error");

        expect(retval).toExist();
        expect(retval.type).toBe(ZONE_SEARCH_ERROR);
        expect(retval.error).toBe("error");
    });

    it('zoneSearch', () => {
        let retval = zoneSearch(true, 1);

        expect(retval).toExist();
        expect(retval.type).toBe(ZONE_SEARCH);
        expect(retval.active).toBe(true);
        expect(retval.id).toBe(1);
    });

    it('loads an existing zones file', (done) => {
        zoneGetValues('../../test-resources/featureGrid-test-data.json')((e) => {
            try {
                expect(e).toExist();
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });

    /*it('openMenu', () => {
        let retval = openMenu(true, 1);

        expect(retval).toExist();
        expect(retval.type).toBe(OPEN_MENU);
        expect(retval.active).toBe(true);
        expect(retval.id).toBe(1);
    });*/

    it('zoneChange', () => {
        let retval = zoneChange(1, "value");

        expect(retval).toExist();
        expect(retval.type).toBe(ZONE_CHANGE);
        expect(retval.value).toBe("value");
        expect(retval.id).toBe(1);
    });

    it('simpleFilterFieldUpdate', () => {
        let retval = simpleFilterFieldUpdate(1, "value");

        expect(retval).toExist();
        expect(retval.type).toBe(SIMPLE_FILTER_FIELD_UPDATE);
        expect(retval.properties).toBe("value");
        expect(retval.id).toBe(1);
    });

    it('addSimpleFilterField', () => {
        let retval = addSimpleFilterField("value");

        expect(retval).toExist();
        expect(retval.type).toBe(ADD_SIMPLE_FILTER_FIELD);
        expect(retval.properties).toBe("value");
    });
    it('removeSimpleFilterField', () => {
        let retval = removeSimpleFilterField(1);

        expect(retval).toExist();
        expect(retval.type).toBe(REMOVE_SIMPLE_FILTER_FIELD);
        expect(retval.id).toBe(1);
    });
    it('removeAllSimpleFilterFields', () => {
        let retval = removeAllSimpleFilterFields();

        expect(retval).toExist();
        expect(retval.type).toBe(REMOVE_ALL_SIMPLE_FILTER_FIELDS);
    });
});
