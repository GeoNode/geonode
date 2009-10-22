{% load i18n %}

if(window.GeoExplorer){
  Ext.apply(GeoExplorer.prototype, {
    zoomSliderTipText :  "{% trans "Zoom Level" %}",
    addLayersButtonText :  "{% trans "Add Layers" %}",
    removeLayerActionText :  "{% trans "Remove Layer" %}",
    zoomToLayerExtentText :  "{% trans "Zoom to Layer Extent" %}",
    removeLayerActionTipText :  "{% trans "Remove Layer" %}",
    layerContainerText :  "{% trans "Map Layers" %}",
    layersPanelText :  "{% trans "Layers" %}",
    layersContainerText :  "{% trans "Data" %}",
    legendPanelText :  "{% trans "Legend" %}",
    capGridText :  "{% trans "Available Layers" %}",
    capGridAddLayersText :  "{% trans "Add Layers" %}",
    capGridDoneText :  "{% trans "Done" %}",
    zoomSelectorText :  "{% trans "Zoom level" %}",
    navActionTipText :  "{% trans "Pan Map" %}",
    navPreviousActionText :  "{% trans "Zoom to Previous Extent" %}",
    navNextAction :  "{% trans "Zoom to Next Extent" %}",
    infoButtonText :  "{% trans "Get Feature Info" %}",
    measureSplitText :  "{% trans "Measure" %}",
    lengthActionText :  "{% trans "Length" %}",
    zoomInActionText :  "{% trans "Zoom In" %}",
    zoomOutActionText :  "{% trans "Zoom Out" %}",
    zoomVisibleButtonText :  "{% trans "Zoom to Visible Extent" %}",
    metaDataHeader:  "{% trans "About this Map" %}",
    metaDataMapTitle:  "{% trans "Title" %}",
    metaDataMapContact:  "{% trans "Contact" %}",
    metaDataMapAbstract:  "{% trans "Abstract" %}",
    metaDataMapTags:  "{% trans "Tags" %}",
    metaDataMapId:  "{% trans "Permalink" %}",
    saveMapText:  "{% trans "Save Map" %}",
    noPermalinkText:  "{% trans "This map has not yet been saved." %}",
    saveFailTitle:  "{% trans "Error While Saving" %}",
    saveFailMessage:  "{% trans "Sorry, your map could not be saved." %}",
    unknownMapTitle:  "{% trans "Unknown Map" %}",
    unknownMapMessage:  "{% trans "Sorry, the map that you are trying to load does not exist.  Creating a new map instead." %}"
  });
}


if(window.Embed){
  Ext.apply(Embed.prototype, {
      zoomLevelText: "{% trans "Zoom Level" %}"
  });
}

if(window.DataPage){
  Ext.apply(DataPage.prototype, {
    dataGridText :  "{% trans "Data" %}",
    dataNameHeaderText :  "{% trans "Name" %}",
    dataTitleHeaderText :  "{% trans "Title" %}",
    dataQueryableHeaderText :  "{% trans "Queryable" %}",
    createMapText :  "{% trans "Create Map" %}",
    openMapText :  "{% trans "Open Map" %}",
    mapTitleLabelText:  "{% trans "Title" %}",
    mapAbstractLabelText:  "{% trans "Abstract" %}",
    mapGridText :  "{% trans "Map" %}",
    ameLabelText:  "{% trans "AME File" %}",
    scenarioLabelText:  "{% trans "Scenario" %}",
    countryLabelText:  "{% trans "Country" %}",
    singularFile:  "{% trans "File" %}",
    pluralFiles:  "{% trans "Files" %}"
  }
  );
}

if(GeoExplorer && GeoExplorer.CapabilitiesGrid){
  Ext.apply(GeoExplorer.CapabilitiesGrid.prototype, {
    nameHeaderText :  "{% trans "Name" %}",
    titleHeaderText :  "{% trans "Title" %}",
    queryableHeaderText :  "{% trans "Queryable" %}"
  });
}

if (ExportWizard) {
    Ext.apply(ExportWizard.prototype, {
        exportDialogMessage:  "{% trans "<p>  Your map is ready to be published to the web! </p> <p> Simply copy the following HTML to embed the map in your website: </p>" %}",
        publishActionText:  "{% trans "Publish Map" %}",
        heightLabel:  "{% trans "Height" %}",
        widthLabel:  "{% trans "Width" %}",
        mapSizeLabel:  "{% trans "Map Size" %}",
        miniSizeLabel:  "{% trans "Mini" %}",
        smallSizeLabel:  "{% trans "Small" %}",
        largeSizeLabel:  "{% trans "Large" %}",
        premiumSizeLabel:  "{% trans "Premium" %}"
    });
}


if(GeoExplorer && GeoExplorer.CapabilitiesRowExpander){
  Ext.apply(GeoExplorer.CapabilitiesRowExpander.prototype, {
    abstractText:  "{% trans "Abstract:" %}",
    downloadText :  "{% trans "Download:" %}",
    metadataText:  "{% trans "Metadata Links:" %}",
    keywordText:  "{% trans "Keywords:" %}",
    attributionText:  "{% trans "Provided by:" %}",
    metadataEmptyText:  "{% trans "No metadata URLs are defined for this layer." %}",
    keywordEmptyText:  "{% trans "No keywords are listed for this layer." %}",
    attributionEmptyText:  "{% trans "No attribution information is provided for this layer." %}"
  });
}
