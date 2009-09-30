

if(window.GeoExplorer){
  Ext.apply(GeoExplorer.prototype, {
      zoomSliderTipText : "Nivel de acercamiento ",
    addLayersButtonText : "Añadir capas",
    removeLayerActionText : "Quitar capa",
    zoomToLayerExtentText : "Acercar a la extension de la capa",
    removeLayerActionTipText : "Quitar capa",
    layerContainerText : "Capas del mapa",
    layersPanelText : "Capas",
    layersContainerText : "Datos",
    legendPanelText : "Descripción",
    capGridText : "Capas disponibiles",
    capGridAddLayersText : "Anadir capas",
    capGridDoneText : "Hecho",
    zoomSelectorText : 'Nivel de acercamiento',
    navActionTipText : "Paneo del mapa",
    navPreviousActionText : "Acercar al grado anterior",
    navNextAction : "Acercar al grado siguiente",
    infoButtonText : "Ver informacion del rasgo",
    measureSplitText : "Medida",
    lengthActionText : "Longitud",
    zoomInActionText : "Acercar",
    zoomOutActionText : "Alejar",
    zoomVisibleButtonText : "Acercar al grado visibile",
    metaDataHeader: 'Sobre este mapa',
    metaDataMapTitle: 'Titolo',
    metaDataMapAbstract: 'Abstracto',
    metaDataMapTags: 'Puntas',
    metaDataMapId: "Permalink",
    saveMapText: "Guardar mapa",
    noPermalinkText: "Este mapa no ha sido todavía guardado.",
    saveFailTitle: "Error guardando",
    saveFailMessage: "Lo siento, tu mapa no ha sido guardado."
  });
}


if(window.HomePage){
  Ext.apply(HomePage.prototype, {
    dataGridText : "Datos",
    dataNameHeaderText : "Nombre",
    dataTitleHeaderText : "Titolo",
    dataQueryableHeaderText : "Consultable",
    createMapText : "Crear mapa",
    openMapText : "Abrir mapa",
    mapTitleLabelText: "Titolo",
    mapAbstractLabelText: "Abstracto",
    mapGridText : "Mapa"
  });
}


if(window.MapGrid){
    Ext.apply(MapGrid.prototype, {
        createMapText : "Crear mapa",
        openMapText : "Abrir mapa",
        mapTitleLabelText: "Titolo",
        mapAbstractLabelText: "Abstracto",
        mapGridText : "Mapa",
        mapLinkLabelText: "UT:View this Map",
        mapTagsLabelText: "UT:Tags"
    });
}



if(window.GeoExplorer && GeoExplorer.CapabilitiesGrid){
  Ext.apply(GeoExplorer.CapabilitiesGrid.prototype, {
    nameHeaderText : "Nombre",
    titleHeaderText : "Titolo",
    queryableHeaderText : "Consultable"
  });
}


if(window.GeoExplorer && GeoExplorer.CapabilitiesRowExpander){
  Ext.apply(GeoExplorer.CapabilitiesRowExpander.prototype, {
    abstractText: "Abstracto:",
    downloadText : "Bajar archivo",
    metadataText: "Enlaces de metadatos:",
    keywordText: "Palabras claves:",
    attributionText: "Proveido por:",
    metadataEmptyText: 'No hay metadatos URLs para esta capa ',
    keywordEmptyText: "No hay palabras claves en lista para esta capa",
    attributionEmptyText: "No hay informacion de attribucion para esta capa."

  });
}

