{% load i18n %}

if (window.GeoExplorer) {
    Ext.apply(GeoExplorer.prototype, {
        addLayersButtonText: gettext("Add Layers"),
        areaActionText: gettext("Area"),
        backgroundContainerText: gettext("Background"),
        capGridAddLayersText: gettext("Add Layers"),
        capGridDoneText: gettext("Done"),
        capGridText: gettext("Available Layers"),
        exportDialogMessage: '<p> UT: Your map is ready to be published to the web! </p>' + '<p> Simply copy the following HTML to embed the map in your website: </p>',
        heightLabel: gettext("Height"),
        infoButtonText: gettext("Get Feature Info"),
        largeSizeLabel: gettext("Large"),
        layerAdditionLabel: gettext("or add a new server."),
        layerContainerText: gettext("Map Layers"),
        layerSelectionLabel: gettext("View available data from:"),
        layersContainerText: gettext("Data"),
        layersPanelText: gettext("Layers"),
        legendPanelText: gettext("Legend"),
        lengthActionText: gettext("Length"),
        mapSizeLabel: gettext("Map Size"), 
        measureSplitText: gettext("Measure"),
        metaDataHeader: gettext("About this Map"),
        metaDataMapAbstract: gettext("Abstract"),
        metaDataMapContact: gettext("Contact"),
        metaDataMapId: gettext("Permalink"),
        metaDataMapTitle: gettext("Title"),
        miniSizeLabel: gettext("Mini"),
        navActionTipText: gettext("Pan Map"),
        navNextAction: gettext("Zoom to Next Extent"),
        navPreviousActionText: gettext("Zoom to Previous Extent"),
        noPermalinkText: gettext("This map has not yet been saved."),
        permalinkLabel: gettext("Permalink"),
        premiumSizeLabel: gettext("Premium"),
        printTipText: gettext("Print Map"),
        printWindowTitleText: gettext("Print Preview"),
        publishActionText: gettext("Publish Map"),
        removeLayerActionText: gettext("Remove Layer"),
        removeLayerActionTipText: gettext("Remove Layer"),
        saveFailMessage: gettext("Sorry, your map could not be saved."),
        saveFailTitle: gettext("Error While Saving"),
        saveMapText: gettext("Save Map"),
        smallSizeLabel: gettext("Small"),
        sourceLoadFailureMessage: gettext("Error contacting server.\n Please check the url and try again."),
        switchTo3DActionText: gettext("Switch to Google Earth 3D Viewer"),
        unknownMapMessage: gettext("The map that you are trying to load does not exist.  Creating a new map instead."),
        unknownMapTitle: gettext("Unknown Map"),
        widthLabel: gettext("Width"),
        zoomInActionText: gettext("Zoom In"),
        zoomOutActionText: gettext("Zoom Out"),
        zoomSelectorText: gettext("Zoom level"),
        zoomSliderTipText: gettext("Zoom Level"),
        zoomToLayerExtentText: gettext("Zoom to Layer Extent"),
        zoomVisibleButtonText: gettext("Zoom to Visible Extent")
    });
}

if (window.Embed) {
  Ext.apply(Embed.prototype, {
      zoomLevelText: gettext("Zoom Level {zoom}")
  });
}

if (window.MapGrid) {
    Ext.apply(MapGrid.prototype, {
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

if (GeoExplorer && GeoExplorer.CapabilitiesGrid) {
    Ext.apply(GeoExplorer.CapabilitiesGrid.prototype, {
        nameHeaderText : gettext("Name"),
        queryableHeaderText : gettext("Queryable"),
        titleHeaderText : gettext("Title")
    });
}

if (ExportWizard) {
    Ext.apply(ExportWizard.prototype, {
        exportDialogMessage: gettext('<p>Your map is ready to be published to the web! </p> <p> Simply copy the following HTML to embed the map in your website: </p>'),
        heightLabel: gettext("Height"),
        largeSizeLabel: gettext("Large"),
        mapSizeLabel: gettext("Map Size"),
        miniSizeLabel: gettext("Mini"),
        premiumSizeLabel: gettext("Premium"),
        publishActionText: gettext("Publish Map"),
        smallSizeLabel: gettext("Small"),
        widthLabel: gettext("Width")
    });
}


if (GeoExplorer && GeoExplorer.CapabilitiesRowExpander) {
    Ext.apply(GeoExplorer.CapabilitiesRowExpander.prototype, {
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

if (GeoExt.ux.PrintPreview) {
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