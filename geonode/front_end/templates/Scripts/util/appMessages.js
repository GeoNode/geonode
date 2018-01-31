var appMessages = {
    toastr: {
        layerAdded: function (layerName) {
            return layerName + " has been added to map.";
        },
        blankLayerAdded: function () {
            return "Blank layer added.";
        },
        layerRemoved: function () {
            return "Layer removed.";
        },
        dataUploaded: function () {
            return "Upload completed.";
        },
        mapSaveAs: function (mapName) {
            return "Map saved as " + mapName + ".";
        },
        mapSaved: function () {
            return "Map saved";
        },
        mapPublishToggled: function(name, published) {
            return "Map " + name + " is " + (published ? "Published" : "Unpublished");
        },
        mapNamedAsUntitled: function (filename) {
            return "Name must not be '" + filename + "'.";
        },
        mapAlreadyOpen: function () {
            return "This map is already open.";
        },
        cannotDeleteOpenMap: function() {
            return "Can't delete an opened map. Please close the map, then try again.";
        },
        mapLocked: function () {
            return 'You have more maps than you are allowed.' +
                ' You need to upgrade your subscription to unlock this project.' +
                ' </br> Go to your profile to check your resource usage.';
        },
        deleted: function (itemName) {
            return itemName + " has been deleted.";
        },
        dataInUse: function () {
            return "The data you have selected is already being used.";
        },
        copied: function (itemName) {
            return "A copy of " + itemName + " has been created.";
        },
        dataLocked: function () {
            return 'You have more data than you are allowed.' +
                ' You need to upgrade your subscription to unlock this data.' +
                ' </br>Go to your profile to check your resource usage.';
        },
        invalidStartCharacter: function () {
            return "Name cannot start with '.'";
        },
        invalidFileNameCharacter: function (character) {
            return "' " + character + " ' is not a valid character for name. Use characters other than / \\ < > : ? * \" |";
        },
        invalidMapName: function (mapName) {
            return "'" + mapName + "' is not a valid name for map. Please choose a different name.";
        },
        unlockAttributeTable: function () {
            return 'Please unlock the table to edit attributes.';
        },
        blankName: function () {
            return "The name cannot be blank. Please choose a valid name.";
        },
        duplicateName: function () {
            return "The name already exists. Please choose a different name.";
        },
        nameChanged: function (newName) {
            return "Name changed to " + newName + ".";
        },
        invalidEmail: function () {
            return "This email address is invalid";
        },
        duplicateEmail: function () {
            return "This email address was already added";
        },
        changesSaved: function () {
            return "Your changes have been saved.";
        },
        unableToSave: function () {
            return "Unable to save changes.";
        },
        saveError: function () {
            return "An error occurred while saving changes.";
        },
        locationServiceDisabled: function () {
            return "Location tracking is disabled for this page.";
        },
        locationNotfound: function () {
            return "The place you are searching for is not found. Please make sure you have spelled correctly.";
        },
        downgradeFailed: function () {
            return "Cannot downgrade a plan";
        },
        userInfoUpdated: function () {
            return "Info updated.";
        },
        userInfoUpdateFailed: function () {
            return "Unable to update info.";
        },
        imagesAdded: function () {
            return "Images Added.";
        },
        filesAdded: function () {
            return "Files Added.";
        },
        imageDeleted: function () {
            return 'Image deleted.';
        },
        fileDeleted: function () {
            return 'Files deleted.';
        },

        deleteImageFailed: function () {
            return 'Failed to remove.';
        },
        imageUploadFailed: function (filename) {
            return 'Could not upload ' + filename;
        },
        createCopyError: function () {
            return "An error occurred while creating copy.";
        },
        deleteFileError: function () {
            return "An error occurred while deleting file.";
        },
        invalidCharacterTitle: function () { return "Invalid character"; },
        upgradeRequiredTitle: function () { return "Upgrade required"; },
        unableToRenameTitle: function () { return "Unable to rename"; },
        unableToStartGpsTitle: function () { return "Could not start GPS"; }
    },
    busyState: {
        addLayer: "Adding Layer...",
        openMap: "Opening Map...",
        deleteItem: "Deleting...",
        apply: "Applying...",
        save: "Saving...",
        createCopy: "Copying..."
    },
    confirm: {
        confirmHeader:"Confirm",
        deleteItem: "Are you sure want to delete this item?",
        deleteItems: "Are you sure want to delete these items?",
        deleteSignleItemFromAttributeGrid:"The associated shape with this row will also be deleted. " +
            "Are you sure want to do this?",
        deleteMultipleItemFromAttributeGrid: "The associated shape with each of this rows will also be deleted. " +
            "Are you sure want to do this?",
        unsavedChange: "There are unsaved changes. Are you sure want to cancel?",
        saveChanges: "Do you want to save your changes?",
        deleteMap: "All layers and other information related to this map will be removed too. </br> Are you sure you want to delete?",
        openNewMap: "Do you want to save your changes before opening new map?",
        mapAlreadyExists: function (mapName) {
            return "A map named " + mapName + " already exists.</br> Do you want to replace it?";
        },
        cancelUploadTitle: "Cancel upload",
        cancelUpload: "Do you want to cancel the upload?",
        clearShapes: "All the shapes will be deleted from the active layer. " +
            "<br/>You can not Undo this action. " +
            "<br/>Are you sure?",
        removeLayerTitle: "Remove Layer",
        removeLayer: "The layer will be deleted from the map. " +
            "<br/>You cannot undo this action. " +
            "<br/>Are you sure?",
        dataSharedAndUsedInMap: "This data is already used in one or more maps and also shared with one or more users. Do you still want to delete this data?",
        dataUsedInMap: "This data is already used in one or more maps. Do you still want to delete this data?",
        dataShared: "This data is shared with one or more users. Do you still want to delete this data?"
    },
    validation: {
        maximumMapLimitReached: "You have reached the maximum number of maps. Please upgrade your subscription to add more maps.",
        maximumBandwidthLimitReached: "You have reached the bandwidth limit for this month."
            + " Please upgrade your profile to upload more files per month.",
        maximumStorageLimitReached: "You have reached the storage limit. Please upgrade your subscription to add more files."
    }
}
