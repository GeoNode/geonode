/**
 * @requires GeoExt/Lang.js
 */

GeoExt.Lang.add("es", {

    "gxp.menu.LayerMenu.prototype": {
        layerText: "Capa"
    },
    
    "gxp.plugins.AddLayers.prototype": {
        addActionMenuText: "Añadir Capas",
        addActionTip: "Añadir Capas",
        addServerText: "Añadir servidor",
        addButtonText: "Añadir Capas",
        untitledText: "Sin Título",
        addLayerSourceErrorText: "Error obteniendo capabilities de WMS ({msg}).\nPor favor, compruebe la URL y vuelva a intentarlo.",
        availableLayersText: "Capas disponibles",
        expanderTemplateText: "<p><b>Resumen:</b> {abstract}</p>",
        panelTitleText: "Título",
        layerSelectionText: "Source:",
        sourceSelectOrTypeText: "Choose one or type service URL",
        doneText: "Hecho",
        uploadText: "Subir Datos"
    },
    
    "gxp.plugins.BingSource.prototype": {
        title: "Capas Bing",
        roadTitle: "Bing Carreteras",
        aerialTitle: "Bing Foto Aérea",
        labeledAerialTitle: "Bing Híbrido"
    },    

    "gxp.plugins.FeatureEditor.prototype": {
        splitButtonText: "Edit",
        createFeatureActionText: "Create",
        editFeatureActionText: "Modify",
        createFeatureActionTip: "Crear nuevo elemento",
        editFeatureActionTip: "Editar elemento existente"
    },
    
    "gxp.plugins.FeatureGrid.prototype": {
        displayFeatureText: "Mostrar en el mapa",
        firstPageTip: "Primera página",
        previousPageTip: "Página anterior",
        zoomPageExtentTip: "Zoom a la extensión de la página",
        nextPageTip: "Página siguiente",
        lastPageTip: "Última página",
        totalMsg: "Features {1} to {2} of {0}"
    },

    "gxp.plugins.GoogleEarth.prototype": {
        menuText: "Vista 3D",
        tooltip: "Vista 3D"
    },
    
    "gxp.plugins.GoogleSource.prototype": {
        title: "Capas Google",
        roadmapAbstract: "Mostrar Callejero",
        satelliteAbstract: "Mostrar imágenes aéreas",
        hybridAbstract: "Mostrar imágenes con nombres de calle",
        terrainAbstract: "Mostrar callejero con terreno"
    },

    "gxp.plugins.LayerProperties.prototype": {
        menuText: "Propiedades de la capa",
        toolTip: "Propiedades de la capa"
    },
    
    "gxp.plugins.LayerTree.prototype": {
        shortTitle: "Capas",
        rootNodeText: "Capas",
        overlayNodeText: "Capas superpuestas",
        baseNodeText: "Capa base"
    },

    "gxp.plugins.LayerManager.prototype": {
        baseNodeText: "Capa base"
    },

    "gxp.plugins.Legend.prototype": { 
        menuText: "Leyenda",
        tooltip: "Leyenda"
    },

    "gxp.plugins.LoadingIndicator.prototype": {
        loadingMapMessage: "Loading Map..."
    },

    "gxp.plugins.MapBoxSource.prototype": {
        title: "MapBox Layers",
        blueMarbleTopoBathyJanTitle: "Blue Marble Topography & Bathymetry (January)",
        blueMarbleTopoBathyJulTitle: "Blue Marble Topography & Bathymetry (July)",
        blueMarbleTopoJanTitle: "Blue Marble Topography (January)",
        blueMarbleTopoJulTitle: "Blue Marble Topography (July)",
        controlRoomTitle: "Control Room",
        geographyClassTitle: "Geography Class",
        naturalEarthHypsoTitle: "Natural Earth Hypsometric",
        naturalEarthHypsoBathyTitle: "Natural Earth Hypsometric & Bathymetry",
        naturalEarth1Title: "Natural Earth I",
        naturalEarth2Title: "Natural Earth II",
        worldDarkTitle: "World Dark",
        worldLightTitle: "World Light",
        worldPrintTitle: "World Print"
    },

    "gxp.plugins.Measure.prototype": {
        buttonText: "Medir",
        lengthMenuText: "Longitud",
        areaMenuText: "Área",
        lengthTooltip: "Medir Longitud",
        areaTooltip: "Medir Área",
        measureTooltip: "Medir"
    },

    "gxp.plugins.Navigation.prototype": {
        menuText: "Desplazar mapa",
        tooltip: "Desplazar mapa"
    },

    "gxp.plugins.NavigationHistory.prototype": {
        previousMenuText: "Vista anterior",
        nextMenuText: "Vista siguiente",
        previousTooltip: "Vista anterior",
        nextTooltip: "Vista siguiente"
    },

    "gxp.plugins.OSMSource.prototype": {
        title: "Capas OpenStreetMap",
        mapnikAttribution: "Datos CC-By-SA de <a href='http://openstreetmap.org/'>OpenStreetMap</a>",
        osmarenderAttribution: "Datos CC-By-SA de <a href='http://openstreetmap.org/'>OpenStreetMap</a>"
    },

    "gxp.plugins.Print.prototype": {
        buttonText:"Imprimir",
        menuText: "Imprimir mapa",
        tooltip: "Imprimir mapa",
        previewText: "Vista previa",
        notAllNotPrintableText: "No se pueden imprimir todas las capas",
        nonePrintableText: "No se puede imprimir ninguna de las capas del mapa"
    },

    "gxp.plugins.MapQuestSource.prototype": {
        title: "Capas MapQuest",
        osmAttribution: "Teselas cortesía de <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        osmTitle: "MapQuest OpenStreetMap",
        naipAttribution: "Teselas cortesía de <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        naipTitle: "MapQuest Imágenes"
    },

    "gxp.plugins.QueryForm.prototype": {
        queryActionText: "Consultar",
        queryMenuText: "Consultar capa",
        queryActionTip: "Consultar la capa seleccionada",
        queryByLocationText: "Query by current map extent",
        queryByAttributesText: "Consultar por atributos",
        queryMsg: "Consultando...",
        cancelButtonText: "Cancelar",
        noFeaturesTitle: "Sin coincidencias",
        noFeaturesMessage: "Su consulta no produjo resultados."
    },

    "gxp.plugins.RemoveLayer.prototype": {
        removeMenuText: "Eliminar Capa",
        removeActionTip: "Eliminar Capa"
    },
    
    "gxp.plugins.Styler.prototype": {
        menuText: "Editar estilos",
        tooltip: "Gestionar estilos de capa"
    },

    "gxp.plugins.WMSGetFeatureInfo.prototype": {
        buttonText:"Identify",
        infoActionTip: "Consultar elementos",
        popupTitle: "Información de elementos"
    },

    "gxp.plugins.Zoom.prototype": {
        zoomMenuText: "Zoom Box",
        zoomInMenuText: "Acercar",
        zoomOutMenuText: "Alejar",
        zoomTooltip: "Zoom by dragging a box",
        zoomInTooltip: "Acercar",
        zoomOutTooltip: "Alejar"
    },
    
    "gxp.plugins.ZoomToExtent.prototype": {
        menuText: "Ver extensión total",
        tooltip: "Ver extensión total"
    },
    
    "gxp.plugins.ZoomToDataExtent.prototype": {
        menuText: "Ver toda la capa",
        tooltip: "Ver toda la capa"
    },

    "gxp.plugins.ZoomToLayerExtent.prototype": {
        menuText: "Ver toda la la capa",
        tooltip: "Ver toda la capa"
    },
    
    "gxp.plugins.ZoomToSelectedFeatures.prototype": {
        menuText: "Ver los elementos seleccionados",
        tooltip: "Ver los elementos seleccionados"
    },

    "gxp.FeatureEditPopup.prototype": {
        closeMsgTitle: "¿Desea guardar los cambios?",
        closeMsg: "Los cambios en este elemento no se han guardado. ¿Desea guardar los cambios?",
        deleteMsgTitle: "¿Desea borrar el elemento?",
        deleteMsg: "¿Está seguro de querer borrar este elemento?",
        editButtonText: "Editar",
        editButtonTooltip: "Hacer editable este elemento",
        deleteButtonText: "Borrar",
        deleteButtonTooltip: "Borrar este elemento",
        cancelButtonText: "Cancelar",
        cancelButtonTooltip: "Dejar de editar, descartar cambios",
        saveButtonText: "Guardar",
        saveButtonTooltip: "Guardar cambios"
    },
    
    "gxp.FillSymbolizer.prototype": {
        fillText: "Relleno",
        colorText: "Color",
        opacityText: "Opacidad"
    },
    
    "gxp.FilterBuilder.prototype": {
        builderTypeNames: ["cualquiera de", "todas", "ninguna de", "no todas"],
        preComboText: "Cumplir",
        postComboText: "las condiciones siguientes:",
        addConditionText: "añadir condición",
        addGroupText: "añadir grupo",
        removeConditionText: "eliminar condición"
    },
    
    "gxp.grid.CapabilitiesGrid.prototype": {
        nameHeaderText : "Nombre",
        titleHeaderText : "Título",
        queryableHeaderText : "Consultable",
        layerSelectionLabel: "Ver datos disponibles de:",
        layerAdditionLabel: "o añadir otro servidor.",
        expanderTemplateText: "<p><b>Resumen:</b> {abstract}</p>"
    },
    
    "gxp.PointSymbolizer.prototype": {
        graphicCircleText: "círculo",
        graphicSquareText: "cuadrado",
        graphicTriangleText: "triángulo",
        graphicStarText: "estrella",
        graphicCrossText: "cruz",
        graphicXText: "x",
        graphicExternalText: "externo",
        urlText: "URL",
        opacityText: "opacidad",
        symbolText: "Símbolo",
        sizeText: "Tamaño",
        rotationText: "Giro"
    },

    "gxp.QueryPanel.prototype": {
        queryByLocationText: "Consultar por localización",
        currentTextText: "Extensión actual",
        queryByAttributesText: "Consultar por atributo",
        layerText: "Capa"
    },
    
    "gxp.RulePanel.prototype": {
        scaleSliderTemplate: "{scaleType} Escala 1:{scale}",
        labelFeaturesText: "Etiquetado de elementos",
        labelsText: "Etiquetas",
        basicText: "Básico",
        advancedText: "Advanzado",
        limitByScaleText: "Limitar por escala",
        limitByConditionText: "Limitar por condición",
        symbolText: "Símbolo",
        nameText: "Nombre"
    },
    
    "gxp.ScaleLimitPanel.prototype": {
        scaleSliderTemplate: "{scaleType} Escala 1:{scale}",
        minScaleLimitText: "Escala mínima",
        maxScaleLimitText: "Escala máxima"
    },
    
    "gxp.StrokeSymbolizer.prototype": {
        solidStrokeName: "continuo",
        dashStrokeName: "guiones",
        dotStrokeName: "puntos",
        titleText: "Trazo",
        styleText: "Estilo",
        colorText: "Color",
        widthText: "Ancho",
        opacityText: "Opacidad"
    },
    
    "gxp.StylePropertiesDialog.prototype": {   
        titleText: "General",
        nameFieldText: "Nombre",
        titleFieldText: "Título",
        abstractFieldText: "Resumen"
    },
    
    "gxp.TextSymbolizer.prototype": {
        labelValuesText: "Etiquetado",
        haloText: "Halo",
        sizeText: "Tamaño"
    },
    
    "gxp.WMSLayerPanel.prototype": {
        aboutText: "Acerca de",
        titleText: "Título",
        nameText: "Nombre",
        descriptionText: "Descripción",
        displayText: "Mostrar",
        opacityText: "Opacidad",
        formatText: "Formato",
        transparentText: "Transparente",
        cacheText: "Caché",
        cacheFieldText: "Usar la versión en caché",
        stylesText: "Estilos",
        infoFormatText: "Info format",
        infoFormatEmptyText: "Select a format"
    },

    "gxp.EmbedMapDialog.prototype": {
        publishMessage: "¡Ya puede publicar su mapa en otras webs! Simplemente copie el siguiente código HTML en el lugar donde desee incrustarlo:",
        heightLabel: 'Alto',
        widthLabel: 'Ancho',
        mapSizeLabel: 'Tamaño',
        miniSizeLabel: 'Mínimo',
        smallSizeLabel: 'Pequeño',
        premiumSizeLabel: 'Premium',
        largeSizeLabel: 'Grande'
    },
    
    "gxp.WMSStylesDialog.prototype": {
        addStyleText: "Añadir",
        addStyleTip: "Añadir un estilo",
        chooseStyleText: "Escoger estilo",
        deleteStyleText: "Quitar",
        deleteStyleTip: "Borrar el estilo seleccionado",
        editStyleText: "Cambiar",
        editStyleTip: "Editar el estilo seleccionado",
        duplicateStyleText: "Clonar",
        duplicateStyleTip: "Duplicar el estilo seleccionado",
        addRuleText: "Añadir",
        addRuleTip: "Añadir una regla",
        newRuleText: "Nueva regla",
        deleteRuleText: "Quitar",
        deleteRuleTip: "Borrar la regla seleccionada",
        editRuleText: "Cambiar",
        editRuleTip: "Editar la regla seleccionada",
        duplicateRuleText: "Duplicar",
        duplicateRuleTip: "Duplicar la regla seleccionada",
        cancelText: "Cancelar",
        saveText: "Guardar",
        styleWindowTitle: "Estilo: {0}",
        ruleWindowTitle: "Regla: {0}",
        stylesFieldsetTitle: "Estilos",
        rulesFieldsetTitle: "Reglas"
    },

    "gxp.LayerUploadPanel.prototype": {
        titleLabel: "Título",
        titleEmptyText: "Título de la capa",
        abstractLabel: "Descripción",
        abstractEmptyText: "Descripción de la capa",
        fileLabel: "Datos",
        fieldEmptyText: "Navegue por los datos...",
        uploadText: "Subir",
        waitMsgText: "Suba sus datos data...",
        invalidFileExtensionText: "El fichero debe tener alguna de estas extensiones: ",
        optionsText: "Opciones",
        workspaceLabel: "Espacio de trabajo",
        workspaceEmptyText: "Espacio de trabajo por defecto",
        dataStoreLabel: "Almacén de datos",
        dataStoreEmptyText: "Create new store",
        defaultDataStoreEmptyText: "Almacén de datos por defecto"
    },
    
    "gxp.NewSourceDialog.prototype": {
        title: "Añadir Servidor...",
        cancelText: "Cancelar",
        addServerText: "Añadir Servidor",
        invalidURLText: "Enter a valid URL to a WMS endpoint (e.g. http://example.com/geoserver/wms)",
        contactingServerText: "Conectando con el Servidor..."
    },

    "gxp.ScaleOverlay.prototype": { 
        zoomLevelText: "Escala"
    },
    
    "gxp.plugins.ArcGISCacheSource.prototype": {
        noLayersTitle: "No ArcGIS Layers",
        noLayersText: "Could not find any layers with a compatible projection (Web Mercator) at "
    },    
    
    "gxp.plugins.ArcRestSource.prototype": {
        noLayersTitle: "No ArcGIS Layers",
        noLayersText: "Could not find any layers with a compatible projection (Web Mercator) at "
    },
    
    "gxp.plugins.MapShare.prototype": { 
    	text: "Share Map",
    	toolTip: "Map info and download links"
    },
    
    "gxp.plugins.AnnotationTool.prototype": {
        errorTitle: "Error creating annotation",
        noteText: "Note",        
        notesText: "Notes",
        showNotesText: "Show notes",
        editNotesText: "Edit notes",       
        addNoteText: "Add note",        
        newNoteText: "New note",
        projection: "EPSG:4326",
        pointText: "Point",
        lineText: "Line",
        polygonText: "Shape",
        saveFailTitle: "Could not save note",
        saveFailText: "Edit failed.  You might not have permission to save this note.",        
        saveText: "Save",        
        editText: "Edit",       
        deleteText: "Delete",        
        cancelText: "Cancel",        
        titleText: "Title"
    },
    
    "gxp.SearchBar.prototype": {
    	emptyText: 'Enter search...',
    	searchText: 'Search',
    	noSearchableLayersTitle: 'No Searchable Layers',
    	noSearchableLayersMsg: 'There are currently no searchable layers on the map.  You must have at least one visible layer with searchable fields on the map.',
    	searchTermTitle: "Search Term Required", 
    	searchTermText: "Please enter a search term",
    	resetText: "Reset"
    },
    
    "gxp.plugins.PrintPage.prototype": {
        menuText: "Print Map",
        tooltip: "Print Map",
        buttonText: "Print"
    },
    
    "gxp.plugins.CoordinateTool.prototype": {
        title: "Map Coordinates (longitude, latitude)",
        infoActionTip: "Get coordinates at the mouse position",
        coordinatePositionText: "CoordinatePosition"
    },
    
    "gxp.plugins.FeedSource.prototype": {
        title: 'Feed Source'
    },
    
    "gxp.plugins.HGLSource.prototype": {
        title: 'Harvard Geospatial Library Source'
    },
    
    "gxp.plugins.HGLFeedSource.prototype" : {
        title: 'HGL Feed Source'
    },
    
    "gxp.plugins.PicasaFeedSource.prototype" : {
        title: 'Picasa Source'
    },
    
    "gxp.plugins.YouTubeFeedSource.prototype" : {
        title: 'YouTube Source'
    },
    
    "gxp.plugins.GeoLocator.prototype": {
        infoActionTip: "Get My Location",
        locationFailedText: "Location detection failed"
    },
    
    "gxp.plugins.LayerShare.prototype": {
        menuText: "Share Layer",
        toolTip: "Layer info and download links"
    },

    "gxp.plugins.MapShare.prototype": {
        text: "Share My Map",
        toolTip: "Map info and download links"
    },    

    "gxp.plugins.AddCategory.prototype": {
        addCategoryMenuText:"Add Category",
        addCategoryActionTipText:"Add a category to the layer tree",
        categoryNameText: "Category name:"
    },    
    
    "gxp.plugins.RemoveCategory.prototype": {
    	removeCategoryActionText:"Remove Category",
    	removeCategoryActionTipText: "Remove this category and all its layers from the map",
    	cannotRemoveText: "This category cannot be removed"
    },
    
    "gxp.plugins.RenameCategory.prototype": {
        renameCategoryActionText:"Rename Category",
        renameCategoryActionTipText:"Give this category a new name",
        cannotRenameText: "This category cannot be renamed"
    },
    
    "gxp.LinkEmbedMapDialog.prototype": {
    	linkMessage: 'Paste link in email or IM'
    },    
    
    "gxp.plugins.GeoNodeQueryTool.prototype" : {
        infoActionTip: "Get Feature Info",
        popupTitle: "Feature Info",
        resetTitle: "Reset",
        resetToolTipText: " Clear all features"
    },
    
    "gxp.plugins.MapRevisionTool.prototype" : {
    	infoActionTip: 'View a list of map revisions',
    	toolText: 'Revisions',
    	windowTitle: "Map Revision History"
    },
    
    "gxp.plugins.GazetteerTool.prototype" : {
        infoActionTip: 'Enter a place name to search for',
        toolText: 'Gazetteer',
        searchingText: 'Searching...',
        fromText: 'From: YYYY-MM-DD',
        toText: 'To: YYYY-MM-DD',
        datesText: 'Dates',
        geocodersText: 'Geocoders', 
        advancedText: 'Advanced',
        sourceText: 'Source',
        startDateText: 'Start Date',
        endDateText: 'End Date',  	
        placenameText: 'Place name',
        coordinatesText: 'Coordinates'  	
    },
    
    "gxp.plugins.StreetViewTool.js" : {
    	toolText: "Google Street View",
    	streetViewTitle: "Google Street View",  	
    	infoActionTip: "Click on the map to see Google Street View"
    }

});
