{% load i18n %}

if (window.GeoExt && GeoExt.Lang) {
    GeoExt.Lang.set("{{ LANGUAGE_CODE }}");
}

if (window.GeoExplorer) {
    Ext.apply(GeoExplorer.prototype, {
        addLayersButtonText: gettext("Add Layers"),
        arcGisRestLabel: gettext("Add ArcGIS REST Server"),
        areaActionText: gettext("Area"),
        backgroundContainerText: gettext("Background"),
        capGridAddLayersText: gettext("Add Layers"),
        capGridDoneText: gettext("Done"),
        capGridText: gettext("Available Layers"),
        connErrorTitleText: gettext("Connection Error"),
        connErrorText: gettext("The server returned an error"),
        connErrorDetailsText: gettext("Details..."),
        exportDialogMessage: '<p>Your map is ready to be published to the web! </p>' + '<p> Simply copy the following HTML to embed the map in your website: </p>',

        feedAdditionLabel: 'Add Feed',
        googleEarthBtnText: gettext("Google Earth"),
        heightLabel: gettext("Height"),
        helpLabel: gettext("Help"),
        infoButtonText: gettext("About"),
        largeSizeLabel: gettext("Large"),
        layerAdditionLabel: gettext("Add another server"),
        layerContainerText: gettext("Map Layers"),
        layerSelectionLabel: gettext("View available data from:"),
        layerLocalLabel: gettext("Upload your own data"),
        
        layersContainerText: gettext("Data"),
        layersPanelText: gettext("Layers"),
        legendPanelText: gettext("Legend"),
        lengthActionText: gettext("Length"),
        loadingMapMessage: gettext("Loading Map..."),
        mapSizeLabel: gettext("Map Size"),
        maxLayersTitle: gettext('Warning'),
        maxLayersText: gettext('You now have %n layers in your map.  With more than %max layers you may experience problems with layer ordering, info balloon display, and general performance.'),
        measureSplitText: gettext("Measure"),
        metaDataHeader: gettext("About this Map View"),
        metaDataMapAbstract: gettext("Abstract (brief description)"),
        metaDataMapKeywords: gettext("Keywords (for Picasa and YouTube overlays)"),
        metaDataMapIntroText: gettext("Introduction (tell visitors more about your map view)"),
        metaDataMapContact: gettext("Contact"),
        metaDataMapId: gettext("Permalink"),
        metadataFormCancelText : gettext("Cancel"),
        metadataFormSaveAsCopyText : gettext("Save as Copy"),
        metadataFormSaveText : gettext("Save"),
        metaDataMapTitle: gettext("Title"),
        metaDataMapUrl: gettext("URL:"),
        miniSizeLabel: gettext("Mini"),
        navActionTipText: gettext("Pan Map"),
        navNextAction: gettext("Zoom to Next Extent"),
        navPreviousActionText: gettext("Zoom to Previous Extent"),
        noPermalinkText: gettext("This map has not yet been saved."),
        permalinkLabel: gettext("Permalink"),
        premiumSizeLabel: gettext("Premium"),
        printTipText: gettext("Print Map"),
        printBtnText: gettext("Print"),
        printWindowTitleText: gettext("Print Preview"),
        propertiesText: gettext("Properties"),
        publishActionText: gettext("Link to Map"),
        publishBtnText: gettext("Link"),
        removeLayerActionText: gettext("Remove Layer"),
        removeLayerActionTipText: gettext("Remove Layer"),
        revisionBtnText: gettext("Revisions"),
        saveFailMessage: gettext("Sorry, your map could not be saved."),
        saveFailTitle: gettext("Error While Saving"),
        saveMapText: gettext("Save Map"),
        saveMapBtnText: gettext("Save"),
        saveMapAsText: gettext("Copy"),
        saveNotAuthorizedMessage: gettext("You must be logged in to save this map."),
        shareLayerText: gettext("Share Layer"),
        shareMapText: gettext("Share Map"),
        smallSizeLabel: gettext("Small"),
        sourceLoadFailureMessage: gettext("Error contacting server.\n Please check the url and try again."),
        streetViewBtnText: gettext("Street View"),
        addCategoryActionText: gettext('Add New Category'),
        addCategoryActionTipText: gettext('Add a new layer category'),
        renameCategoryActionText: gettext('Rename Category'),
        renameCategoryActionTipText: gettext('Rename this category'),    
        removeCategoryActionText: gettext('Remove Category'),
        removeCategoryActionTipText: gettext('Remove this category and layers'),
        layerPropertiesText: gettext('Layer Properties'),
        layerPropertiesTipText: gettext('Change layer format and style'),
        layerStylesText: gettext('Edit Styles'),
        layerStylesTipText: gettext('Edit layer styles'),
        switchTo3DActionText: gettext("Switch to Google Earth 3D Viewer"),
        unknownMapMessage: gettext("The map that you are trying to load does not exist.  Creating a new map instead."),
        unknownMapTitle: gettext("Unknown Map"),
        widthLabel: gettext("Width"),
        zoomInActionText: gettext("Zoom In"),
        zoomOutActionText: gettext("Zoom Out"),
        zoomSelectorText: gettext("Zoom level"),
        zoomSliderTipText: gettext("Zoom Level"),
        zoomToLayerExtentText: gettext("Zoom to Layer Extent"),
        zoomVisibleButtonText: gettext("Zoom to Original Map Extent"),
        flickrText: gettext("Flickr"),
        picasaText: gettext("Picasa"),
        youTubeText: gettext("YouTube"),
        hglText: gettext("Harvard Geospatial Library"),
        moreText: gettext("More..."),
        uploadLayerText: gettext('Upload Layer'),
        createLayerText: gettext('Create Layer'),
        rectifyLayerText: gettext('Rectify Layer'),
        worldmapDataText:  gettext('WorldMap Data'),
        externalDataText: gettext('External Data'),
        leavePageWarningText: gettext('If you leave this page, unsaved changes will be lost.')
    });
}

if (window.Embed) {
  Ext.apply(Embed.prototype, {
      zoomLevelText: gettext("Zoom Level {zoom}")
  });
}

if (window.GeoNode && GeoNode.MapGrid) {
    Ext.apply(GeoNode.MapGrid.prototype, {
        createMapText : gettext("Create Map"),
        exportMapText: gettext("Export Map"),
        mapAbstractLabelText: gettext("Abstract"),
        mapContactLabelText: gettext("Contact"),
        mapGridText : gettext("Map"),
        mapLinkLabelText: gettext("View this Map"),
        mapTitleLabelText: gettext("Title"),
        openMapText : gettext("Open Map")
    });
}

if (window.GeoExplorer && GeoExplorer.CapabilitiesGrid) {
    Ext.apply(GeoExplorer.CapabilitiesGrid.prototype, {
        nameHeaderText : gettext("Name"),
        queryableHeaderText : gettext("Queryable"),
        titleHeaderText : gettext("Title")
    });
}

if (window.GeoNode && GeoNode.ConfigManager) {
    Ext.apply(GeoNode.ConfigManager.prototype, {
        backgroundDisabledText : gettext("No background")
    });
}

if (window.gxp && gxp.EmbedMapDialog) {
    Ext.apply(gxp.EmbedMapDialog.prototype, {
        heightLabel: gettext("Height"),
        largeSizeLabel: gettext("Large"),
        mapSizeLabel: gettext("Map Size"),
        miniSizeLabel: gettext("Mini"),
        premiumSizeLabel: gettext("Premium"),
        publishActionText: gettext("Publish Map"),
        publishMessage: gettext('Your map is ready to be published to the web!  Simply copy the following HTML to embed the map in your website:'),
        smallSizeLabel: gettext("Small"),
        widthLabel: gettext("Width")
    });
}

if (window.GeoExplorer && GeoExplorer.CapabilitiesRowExpander) {
    Ext.apply(GeoExplorer.CapabilitiesRowExpander.prototype, {
    	categoryText: gettext("Category:"),
        abstractText: gettext("Abstract:"),
        attributionEmptyText: gettext("No attribution information is provided for this layer."),
        attributionText: gettext("Provided by:"),
        downloadText : gettext("Download:"),
        keywordEmptyText: gettext("No keywords are listed for this layer."),
        keywordText: gettext("Keywords:"),
        metadataEmptyText: gettext("No metadata URLs are defined for this layer."),
        metadataText: gettext("Metadata Links:")
    });
}

if (window.GeoExt && GeoExt.ux && GeoExt.ux.PrintPreview) {
    Ext.apply(GeoExt.ux.PrintPreview.prototype, {
        paperSizeText: gettext("Paper size:"),
        resolutionText: gettext("Resolution:"),
        printText: gettext("Print"),
        emptyTitleText: gettext("Enter map title here."),
        includeLegendText: gettext("Include legend?"),
        emptyCommentText: gettext("Enter comments here."),
        creatingPdfText: gettext("Creating PDF...")
    });
}


if (window.GeoNode && GeoNode.MapSearchTable) {
    Ext.apply(GeoNode.MapSearchTable.prototype, {
        titleHeaderText: gettext('Title'),
        contactHeaderText: gettext("Contact"),
        lastModifiedHeaderText: gettext("Last Modified"),
        mapAbstractLabelText: gettext("Abstract"),
        mapLinkLabelText: gettext("View this Map"),
        previousText: gettext('Prev'),
        nextText: gettext('Next'),
        ofText: gettext('of'),
        noResultsText: gettext('Your search did not match any items.'),
        searchLabelText: gettext('Search Maps'),
        searchButtonText: gettext('Search'),
        showingText: gettext('Showing'),
        loadingText: gettext('Loading'),
        permalinkText: gettext('permalink')
    });
}


if (window.GeoNode && GeoNode.SearchTable) {
    Ext.apply(GeoNode.SearchTable.prototype, {
        selectHeaderText: gettext('Select'),
        nameHeaderText: gettext('Name'),
        titleHeaderText: gettext('Title'),
        selectText: gettext('Select:'),
        selectAllText: gettext('All'),
        selectNoneText: gettext('None'),
        previousText: gettext('Prev'),
        nextText: gettext('Next'),
        ofText: gettext('of'),
        noResultsText: gettext('Your search did not match any items.'),
        searchButtonText: gettext('Search'),
        showingText: gettext('Showing'),
        loadingText: gettext("Loading..."),
        permalinkText: gettext('permalink'),
        unviewableTooltip: gettext('You do not have permission to view this data'),
        remoteTooltip: gettext('This data is stored on a remote server')    
    });
}
if (window.GeoNode && GeoNode.SearchTableRowExpander) {
    Ext.apply(GeoNode.SearchTableRowExpander.prototype, {
    	categoryText:gettext("Category"),
    	categoryEmptyText:gettext('No category is provided for this layer.'),
        abstractText: gettext("Abstract:"),
        abstractEmptyText: gettext('No abstract is provided for this layer.'),
        attributionEmptyText: gettext("No attribution information is provided for this layer."),
        attributionText: gettext("Provided by:"),
        downloadText : gettext("Download:"),
        downloadEmptyText: gettext("No download URLs are definied for this layer."),
        keywordEmptyText: gettext("No keywords are listed for this layer."),
        keywordText: gettext("Keywords:"),
        metadataEmptyText: gettext("No metadata URLs are defined for this layer."),
        metadataText: gettext("Metadata Links:"),
        dataDetailText: 'Click here for more information about this layer.'
    });
}
if (window.GeoNode && GeoNode.DataCart) {
    Ext.apply(GeoNode.DataCart.prototype, {
        selectedLayersText: gettext('Selected Layers'),
        emptySelectionText: gettext('No Layers Selected'),
        titleText: gettext('Title'),
        clearSelectedButtonText: gettext('Clear Selected'),
        clearAllButtonText: gettext('Clear All'),
        addLayersButtonText: gettext('Add Selected Layers')
    });
}

if (window.GeoNode && GeoNode.DataCartOps) {
    Ext.apply(GeoNode.DataCartOps.prototype, {
        failureText: gettext('Operation Failed'),
        noLayersText: gettext('No layers are currently selected.')
    });
}


if (window.GeoNode && GeoNode.BatchDownloadWidget) {
    Ext.apply(GeoNode.BatchDownloadWidget.prototype, {
        downloadingText: gettext('Downloading...'),
        cancelText: gettext('Cancel'),
        windowMessageText: gettext('Please wait')
    });
}

if (window.GeoExplorer && GeoExplorer.ViewerPrint) {
	Ext.apply(GeoExplorer.ViewerPrint.prototype, {
		printMsg: gettext("Press OK to print this page as is.  \
			 If you would like to adjust the map extent, press Cancel, \
			 then use your browser's print button when you are ready"),
		printTitle: gettext("Print")
	});
}

{% block extra_lang %}
{% endblock %}
