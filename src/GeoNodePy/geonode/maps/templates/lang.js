{% load i18n %}

if(window.GeoExplorer){
  Ext.apply(GeoExplorer.prototype, {
    zoomSliderTipText :  gettext("Zoom Level"),
    addLayersButtonText :  gettext("Add Layers"),
    removeLayerActionText :  gettext("Remove Layer"),
    zoomToLayerExtentText :  gettext("Zoom to Layer Extent"),
    removeLayerActionTipText :  gettext("Remove Layer"),
    layerContainerText :  gettext("Map Layers"),
    layersPanelText :  gettext("Layers"),
    layersContainerText :  gettext("Data"),
    legendPanelText :  gettext("Legend"),
    capGridText :  gettext("Available Layers"),
    capGridAddLayersText :  gettext("Add Layers"),
    capGridDoneText :  gettext("Done"),
    zoomSelectorText :  gettext("Zoom level"),
    navActionTipText :  gettext("Pan Map"),
    navPreviousActionText :  gettext("Zoom to Previous Extent"),
    navNextAction :  gettext("Zoom to Next Extent"),
    infoButtonText :  gettext("Get Feature Info"),
    measureSplitText :  gettext("Measure"),
    lengthActionText :  gettext("Length"),
    zoomInActionText :  gettext("Zoom In"),
    zoomOutActionText :  gettext("Zoom Out"),
    zoomVisibleButtonText :  gettext("Zoom to Visible Extent"),
    metaDataHeader:  gettext("About this Map"),
    metaDataMapTitle:  gettext("Title"),
    metaDataMapContact:  gettext("Contact"),
    metaDataMapAbstract:  gettext("Abstract"),
    metaDataMapId:  gettext("Permalink"),
    saveMapText:  gettext("Save Map"),
    noPermalinkText:  gettext("This map has not yet been saved."),
    saveFailTitle:  gettext("Error While Saving"),
    saveFailMessage:  gettext("Sorry, your map could not be saved."),
    unknownMapTitle:  gettext("Unknown Map"),
    unknownMapMessage:  gettext("Sorry, the map that you are trying to load does not exist.  Creating a new map instead."),
      switchTo3DActionText: gettext("Switch to Google Earth 3D Viewer"),
      publishActionText: gettext('Publish Map')

  });
}


if(window.Embed){
  Ext.apply(Embed.prototype, {
      zoomLevelText: gettext("Zoom Level")
  });
}

if(window.DataPage){
  Ext.apply(DataPage.prototype, {
    dataGridText :  gettext("Data"),
    dataNameHeaderText :  gettext("Name"),
    dataTitleHeaderText :  gettext("Title"),
    dataQueryableHeaderText :  gettext("Queryable"),
    createMapText :  gettext("Create Map"),
    openMapText :  gettext("Open Map"),
    mapTitleLabelText:  gettext("Title"),
    mapAbstractLabelText:  gettext("Abstract"),
    mapGridText :  gettext("Map"),
    ameLabelText:  gettext("AME File"),
    scenarioLabelText:  gettext("Hazard"),
    countryLabelText:  gettext("Country"),
    singularFile:  gettext("File"),
    pluralFiles:  gettext("Files"),
    noAssociatedLayerFilesText: 'No associated layer tiles.',
    associatedLayerFilesText: "Associated layer files (as GeoTiff): "
  });
}


if(window.MapGrid){
    Ext.apply(MapGrid.prototype, {
        mapGridText : gettext("Map"),
        createMapText : gettext("Create Map"),
        openMapText : gettext("Open Map"),
        exportMapText: gettext("Export Map"),
        mapTitleLabelText: gettext("Title"),
        mapAbstractLabelText: gettext("Abstract"),
        mapContactLabelText: gettext("Contact"),
        mapLinkLabelText: gettext("View this Map")
    });
}



if(GeoExplorer && GeoExplorer.CapabilitiesGrid){
  Ext.apply(GeoExplorer.CapabilitiesGrid.prototype, {
    nameHeaderText :  gettext("Name"),
    titleHeaderText :  gettext("Title"),
    queryableHeaderText :  gettext("Queryable"),
    layerSelectionLabel: gettext("View available data from: "), 
    layerAdditionLabel: gettext("or add a new server")
  });
}

if (ExportWizard) {
    Ext.apply(ExportWizard.prototype, {
        exportDialogMessage:  gettext("<p>  Your map is ready to be published to the web! </p> <p> Simply copy the following HTML to embed the map in your website: </p>"),
        publishActionText:  gettext("Publish Map"),
        heightLabel:  gettext("Height"),
        widthLabel:  gettext("Width"),
        mapSizeLabel:  gettext("Map Size"),
        miniSizeLabel:  gettext("Mini"),
        smallSizeLabel:  gettext("Small"),
        largeSizeLabel:  gettext("Large"),
        premiumSizeLabel:  gettext("Premium")
    });
}


if (GeoExplorer && GeoExplorer.NewSourceWindow) {
    Ext.apply(GeoExplorer.NewSourceWindow.prototype, {
        sourceLoadFailureMessage: 
        gettext('GeoExplorer was unable to read the capabilities document provided. Please verify the service URL and try again.')
    });
}


if(GeoExplorer && GeoExplorer.CapabilitiesRowExpander){
  Ext.apply(GeoExplorer.CapabilitiesRowExpander.prototype, {
    abstractText:  gettext("Abstract:"),
    downloadText :  gettext("Download:"),
    metadataText:  gettext("Metadata Links:"),
    keywordText:  gettext("Keywords:"),
    attributionText:  gettext("Provided by:"),
    metadataEmptyText:  gettext("No metadata URLs are defined for this layer."),
    keywordEmptyText:  gettext("No keywords are listed for this layer."),
      attributionEmptyText:  gettext("No attribution information is provided for this layer."),
    publishActionText: 'Publish Map'
  });
}
