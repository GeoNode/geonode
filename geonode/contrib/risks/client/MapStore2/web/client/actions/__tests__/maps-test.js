/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    // CREATE_THUMBNAIL, createThumbnail,
    MAP_UPDATING, mapUpdating,
    PERMISSIONS_UPDATED, permissionsUpdated,
    ATTRIBUTE_UPDATED, attributeUpdated,
    SAVE_MAP, saveMap,
    DISPLAY_METADATA_EDIT, onDisplayMetadataEdit,
    RESET_UPDATING, resetUpdating,
    THUMBNAIL_ERROR, thumbnailError,
    RESET_CURRENT_MAP, resetCurrentMap,
    MAPS_SEARCH_TEXT_CHANGED, mapsSearchTextChanged,
    MAPS_LIST_LOAD_ERROR, loadError,
    MAP_ERROR, mapError,
    MAP_METADATA_UPDATED, mapMetadataUpdated
} = require('../maps');

describe('Test correctness of the maps actions', () => {

    it('mapUpdating', () => {
        let resourceId = 13;
        var retval = mapUpdating(resourceId);
        expect(retval).toExist();
        expect(retval.type).toBe(MAP_UPDATING);
        expect(retval.resourceId).toBe(resourceId);
    });

    it('permissionsUpdated', () => {
        let resourceId = 13;
        var retval = permissionsUpdated(resourceId, null);
        expect(retval).toExist();
        expect(retval.type).toBe(PERMISSIONS_UPDATED);
        expect(retval.resourceId).toBe(resourceId);
    });

    it('attributeUpdated', () => {
        let resourceId = 13;
        let name = "thumbnail";
        let value = "exampleDataUri";
        let type = "STRING";
        let retval = attributeUpdated(resourceId, name, value, type);
        expect(retval).toExist();
        expect(retval.type).toBe(ATTRIBUTE_UPDATED);
        expect(retval.resourceId).toBe(resourceId);
        expect(retval.name).toBe(name);
        expect(retval.value).toBe(value);
    });

    it('thumbnailError', () => {
        let resourceId = 1;
        let error = {status: 404, message: "not found"};
        let retval = thumbnailError(resourceId, error);
        expect(retval).toExist();
        expect(retval.type).toBe(THUMBNAIL_ERROR);
        expect(retval.resourceId).toBe(resourceId);
        expect(retval.error.status).toBe(error.status);
    });

    it('resetUpdating', () => {
        let resourceId = 1;
        let retval = resetUpdating(resourceId);
        expect(retval).toExist();
        expect(retval.type).toBe(RESET_UPDATING);
        expect(retval.resourceId).toBe(resourceId);
    });

    it('onDisplayMetadataEdit', () => {
        let dispMetadataValue = true;
        let retval = onDisplayMetadataEdit(dispMetadataValue);
        expect(retval).toExist();
        expect(retval.type).toBe(DISPLAY_METADATA_EDIT);
        expect(retval.displayMetadataEditValue).toBe(dispMetadataValue);
    });

    it('saveMap', () => {
        let thumbnail = "myThumnbnailUrl";
        let resourceId = 13;
        let map = {
            thumbnail: thumbnail,
            id: 123,
            canWrite: true
        };
        var retval = saveMap(map, resourceId);
        expect(retval).toExist();
        expect(retval.type).toBe(SAVE_MAP);
        expect(retval.resourceId).toBe(resourceId);
        expect(retval.map).toBe(map);
    });
    it('resetCurrentMap', () => {
        const a = resetCurrentMap();
        expect(a.type).toBe(RESET_CURRENT_MAP);
    });
    it('mapsSearchTextChanged', () => {
        const a = mapsSearchTextChanged("TEXT");
        expect(a.type).toBe(MAPS_SEARCH_TEXT_CHANGED);
        expect(a.text).toBe("TEXT");
    });
    it('loadError', () => {
        const a = loadError();
        expect(a.type).toBe(MAPS_LIST_LOAD_ERROR);
    });
    it('mapError', () => {
        const a = mapError("error");
        expect(a.type).toBe(MAP_ERROR);
        expect(a.error).toBe("error");
    });
    it('mapMetadataUpdated', () => {
        const a = mapMetadataUpdated("resourceId", "newName", "newDescription", "result", "error");
        expect(a.type).toBe(MAP_METADATA_UPDATED);
        expect(a.resourceId).toBe("resourceId");
        expect(a.newName).toBe("newName");
        expect(a.newDescription).toBe("newDescription");
        expect(a.result).toBe("result");
        expect(a.error).toBe("error");
    });
});
