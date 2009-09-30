

if(window.GeoExplorer){
  Ext.apply(GeoExplorer.prototype, {
      zoomSliderTipText : "Zoom Level",
    addLayersButtonText : "Add Layers",
    removeLayerActionText : "Remove Layer",
    zoomToLayerExtentText : "Zoom to Layer Extent",
    removeLayerActionTipText : "Remove Layer",
    layerContainerText : "Map Layers",
    layersPanelText : "Layers",
    layersContainerText : "Data",
    legendPanelText : "Legend",
    capGridText : "Available Layers",
    capGridAddLayersText : "Add Layers",
    capGridDoneText : "Done",
    zoomSelectorText : 'Zoom level',
    navActionTipText : "Pan Map",
    navPreviousActionText : "Zoom to Previous Extent",
    navNextAction : "Zoom to Next Extent",
    infoButtonText : "Get Feature Info",
    measureSplitText : "Measure",
    lengthActionText : "Length",
    zoomInActionText : "Zoom In",
    zoomOutActionText : "Zoom Out",
    zoomVisibleButtonText : "Zoom to Visible Extent",
    metaDataHeader: 'About this Map',
    metaDataMapTitle: 'Title',
    metaDataMapContact: 'Contact',
    metaDataMapAbstract: 'Abstract',
    metaDataMapTags: 'Tags',
    metaDataMapId: "Permalink",
    saveMapText: "Save Map",
    noPermalinkText: "This map has not yet been saved.",
    saveFailTitle: "Error While Saving",
    saveFailMessage: "Sorry, your map could not be saved.",
    unknownMapTitle: "Unknown Map",
    unknownMapMessage: "Sorry, the map that you are trying to load does not exist.  Creating a new map instead."
  });
}


if(window.Embed){
  Ext.apply(Embed.prototype, {
      zoomLevelText : "Zoom Level"
  });
}



if (window.Page) {
    Page.prototype.page = Page.prototype.page || {};
    Ext.apply(Page.prototype.page, {
        header: '<h1>CAPRA: Central American Probabilistic Risk Assessment GeoNode</h1>',
        featuredLink: 'CAPRA Maps',
        indexLink: 'Featured Map',
        communityLink: 'Contributed Maps',
        dataLink: 'Data',
        developerLink: 'OGC Services',
        helpLink: 'Help'
    });
}


if(window.DataPage){
  Ext.apply(DataPage.prototype, {
    dataGridText : "Data",
    dataNameHeaderText : "Name",
    dataTitleHeaderText : "Title",
    dataQueryableHeaderText : "Queryable",
    createMapText : "Create Map",
    openMapText : "Open Map",
    mapTitleLabelText: "Title",
    mapAbstractLabelText: "Abstract",
    mapGridText : "Map",
    ameLabelText: 'AME File',
    scenarioLabelText: 'Scenario',
    countryLabelText: 'Country',
    singularFile: 'File',
    pluralFiles: 'Files'
  }
  );
  DataPage.prototype.page = DataPage.prototype.page || {};
  Ext.apply(DataPage.prototype.page, {
    "risk-description":  '<h3>Risk Data</h3>' +
        '<div>Lorem ipsum, etc.</div>',
    'overlay-description': '<h3>Overlay data</h3>' + 
        '<div> Lorem ipsum etc. </div>', 
    sidebar: '<h2>Welcome to CAPRA\'s GeoNode</h2>' +
        '<p>The GeoNode is a data clearing house for CAPRA.  Currently a ' + 
        'prototype, it provides tools for the distribution and ' + 
        'composition of hazard and risk map data.  Its purpose is to ' + 
        'inform decisions about future data management developments for ' + 
        'CAPRA.</p>'
  });
}

if(window.FeaturedPage){
  FeaturedPage.prototype.page = FeaturedPage.prototype.page || {};
  Ext.apply(FeaturedPage.prototype.page, {
        'map-description': '<h3> CAPRA Maps </h3>' + 
            '<div> The following list shows particularly interesting or ' +
            'effective maps selected by the CAPRA team. See ' + 
            '<a href="community.html">the community map list</a> for other ' + 
            'maps created by GeoNode users. </div>',
        sidebar: '<h2> Welcome to CAPRA\'s GeoNode</h2>' + 
            '<p> The GeoNode is a data clearing house for CAPRA.  Currently ' +
            'a prototype, it provides tools for the distribution and ' + 
            'composition of hazard and risk map data. Its purpose is to ' + 
            'inform decisions about future data management developments ' + 
            'for CAPRA.'
    });
}


if(window.CommunityPage){
  CommunityPage.prototype.page = CommunityPage.prototype.page || {};
  Ext.apply(CommunityPage.prototype.page, {
        'map-description': '<h3>Contributed Maps </h3>' + 
            '<div> <p>Community maps are contributed by users like you.</p></div>',
        sidebar: '<h2> Welcome to CAPRA\'s GeoNode</h2>' + 
            '<p> The GeoNode is a data clearing house for CAPRA.  Currently ' +
            'a prototype, it provides tools for the distribution and ' + 
            'composition of hazard and risk map data. Its purpose is to ' + 
            'inform decisions about future data management developments ' + 
            'for CAPRA.'
    });
}

if(window.MapGrid){
    Ext.apply(MapGrid.prototype, {
        mapGridText : "Map",
        createMapText : "Create Map",
        openMapText : "Open Map",
        exportMapText: "Export Map",
        mapTitleLabelText: "Title",
        mapAbstractLabelText: "Abstract",
        mapContactLabelText: "Contact",
        mapTagsLabelText: "Tags",
        mapLinkLabelText: "View this Map"
    });
}


if (window.DeveloperPage) {
    DeveloperPage.prototype.page = DeveloperPage.prototype.page || {};
    Ext.apply(DeveloperPage.prototype.page, {
        main: '<h3> What are OGC Services? </h3>' +
            '<p> The data in this application is served using open standards endorsed by the <a href="http://opengeospatial.org/">Open Geospatial Consortium</a>; in particular, <a href="http://opengeospatial.org/standards/wms">WMS</a> (the Web Mapping Service) is used for accessing maps and <a href="http://opengeospatial.org/standards/wfs">WFS</a> (the Web Feature Service) is used for accessing data.  You can use these services in your own applications using libraries such as <a href="http://openlayers.org/">OpenLayers</a>, <a href="http://geotools.org/">GeoTools</a>, and <a href="http://www.gdal.org/ogr/">OGR</a> (all of which are open-source software and available at zero cost).' +
            '</p>' +
            '<h3> OpenLayers Example Code </h3>' +
            '<p>To include a CAPRA map layer in an OpenLayers map, first find the name for that layer (available in the \'name\' field (not title) of the layer list.  For this example, we will use the Central American political boundaries background layer, whose name is \'overlay:CA\'.  Then, create an instance of OpenLayers.Layer.WMS:</p>' +
            '<code>' +
                'var capraLayer = new OpenLayers.Layer.WMS("CAPRA Risk Data", ' +
                    '"http://capra.opengeo.org/geoserver/wms",' +
                    '{ layers: "overlay:CA" });' +
            '</code>' +
            '<h3> GeoTools Example Code </h3>' +
            '<p> Create a DataStore and extract a FeatureType from it, then run a Query. It\'s all documented on the wiki at <a href="http://geotools.org/">http://geotools.org/</a> .</p>',
 
        sidebar: '<h3>What is a Sidebar?</h3>' +
          '<h2>CAPRA\'s OGC Services</h2>' +
          '<p>CAPRA\'s OGC Services are available from the following URLs:' +
          '    <li> <strong>WMS</strong>: <a href="http://capra.opengeo.org/geoserver/wms">http://capra.opengeo.org/geoserver/wms</a> </li>' +
          '    <li> <strong>WFS</strong>: <a href="http://capra.opengeo.org/geoserver/wfs">http://capra.opengeo.org/geoserver/wms</a> </li>' +
          '</p>'
    });
}

if (window.IndexPage) {
    IndexPage.prototype.page = IndexPage.prototype.page || {};
    Ext.apply(IndexPage.prototype.page, {
        description: '<h3> Welcome! </h3>',
        sidebar: '<h3> Welcome to CAPRA\'s GeoNode</h3>' + 
            '<p> The GeoNode is a data clearing house for CAPRA.  Currently ' +
            'a prototype, it provides tools for the distribution and ' + 
            'composition of hazard and risk map data. Its purpose is to ' + 
            'inform decisions about future data management developments ' + 
            'for CAPRA.'
    });
}


if(window.HelpPage){
    HelpPage.prototype.page = HelpPage.prototype.page || {};
    Ext.apply(HelpPage.prototype.page, {
        main: '<h3> Using the GeoNode </h3>' +
            'The CAPRA GeoNode provides access to risk data as well as particular refined data sets which can be freely combined to create maps that visualize particular risks for specific regions.  The GeoNode consists of three main sections:' +
            '<ul>' +
            '<li> <strong>A map browser</strong> that allows you to explore the maps already contributed by the community.  There is also a <strong>featured map browser</strong> which highlights particularly effective or interesting maps selected by CAPRA. </li>' +
            '<li> <strong>A data browser</strong> that allows you to view the individual data sets that are available.  You can use these data sets to create your own maps. </li>' +
            '<li> <strong>A map editor</strong> that lets you view maps created by others, create your own maps either from scratch or by customizing maps created by the community, and share your maps with the CAPRA community. </li>' +
            '</ul>',
        sidebar: '<h3>What is a Sidebar?</h3>' +
            '<p>The sidebar contains useful information about the current page. </p>'    
    });
}

if(GeoExplorer && GeoExplorer.CapabilitiesGrid){
  Ext.apply(GeoExplorer.CapabilitiesGrid.prototype, {
    nameHeaderText : "Name",
    titleHeaderText : "Title",
    queryableHeaderText : "Queryable"
  });
}

if (ExportWizard) {
    Ext.apply(ExportWizard.prototype, {
        exportDialogMessage: '<p>  Your map is ready to be published to the web! </p>' +
            '<p> Simply copy the following HTML to embed the map in your website: </p>',
        publishActionText: 'Publish Map',
        heightLabel: 'Height',
        widthLabel: 'Width',
        mapSizeLabel: 'Map Size',
        miniSizeLabel: 'Mini',
        smallSizeLabel: 'Small',
        largeSizeLabel: 'Large',
        premiumSizeLabel: 'Premium'
    });
}


if(GeoExplorer && GeoExplorer.CapabilitiesRowExpander){
  Ext.apply(GeoExplorer.CapabilitiesRowExpander.prototype, {
    abstractText: "Abstract:",
    downloadText : "Download:",
    metadataText: "Metadata Links:",
    keywordText: "Keywords:",
    attributionText: "Provided by:",
    metadataEmptyText: 'No metadata URLs are defined for this layer.',
    keywordEmptyText: "No keywords are listed for this layer.",
    attributionEmptyText: "No attribution information is provided for this layer."  });
}
