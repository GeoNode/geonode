/**
 * @requires GeoExt/Lang.js
 */

GeoExt.Lang.add("ca", {

    "gxp.menu.LayerMenu.prototype": {
        layerText: "Capa"
    },
    
    "gxp.plugins.AddLayers.prototype": {
        addActionMenuText: "Afegeix Capes",
        addActionTip: "Afegeix Capes",
        addServerText: "Afegeix servidor",
        addButtonText: "Afegeix Capes",
        untitledText: "Sense Títol",
        addLayerSourceErrorText: "Error obtenint les capabilities del WMS ({msg}).\nSi us plau, comproveu la URL i torneu-ho a intentar.",
        availableLayersText: "Capes disponibles",
        expanderTemplateText: "<p><b>Resum:</b> {abstract}</p>",
        panelTitleText: "Títol",
        layerSelectionText: "Source:",
        sourceSelectOrTypeText: "Choose one or type service URL",
        doneText: "Fet",
        uploadText: "Puja dades"
    },
    
    "gxp.plugins.BingSource.prototype": {
        title: "Capes Bing",
        roadTitle: "Bing Carrerer",
        aerialTitle: "Bing Fotografia Aèria",
        labeledAerialTitle: "Bing Fotografia Aèria amb Etiquetes"
    },    

    "gxp.plugins.FeatureEditor.prototype": {
        splitButtonText: "Edit",
        createFeatureActionText: "Create",
        editFeatureActionText: "Modify",
        createFeatureActionTip: "Crea nou element",
        editFeatureActionTip: "Edita element existent"
    },
    
    "gxp.plugins.FeatureGrid.prototype": {
        displayFeatureText: "Mostra al mapa",
        firstPageTip: "Primera pàgina",
        previousPageTip: "Pàgina anterior",
        zoomPageExtentTip: "Ajusta vista a l'extensió de la pàgina",
        nextPageTip: "Pàgina següent",
        lastPageTip: "Pàgina anterior",
        totalMsg: "Features {1} to {2} of {0}"
    },

    "gxp.plugins.GoogleEarth.prototype": { 
        menuText: "Vista 3D",
        tooltip: "Vista 3D"
    },
    
    "gxp.plugins.GoogleSource.prototype": {
        title: "Capes Google",
        roadmapAbstract: "Mostra carrerer",
        satelliteAbstract: "Mostra imatges de satèl·lit",
        hybridAbstract: "Mostra imatges amb noms de carrer",
        terrainAbstract: "Mostra carrerer amb terreny"
    },

    "gxp.plugins.LayerProperties.prototype": {
        menuText: "Propietats de la capa",
        toolTip: "Propietats de la capa"
    },
    
    "gxp.plugins.LayerTree.prototype": {
        shortTitle: "Capes",
        rootNodeText: "Capes",
        overlayNodeText: "Capes addicionals",
        baseNodeText: "Capa base"
    },

    "gxp.plugins.LayerManager.prototype": {
        baseNodeText: "Capa base"
    },

    "gxp.plugins.Legend.prototype": { 
        menuText: "Mostra Llegenda",
        tooltip: "Mostra Llegenda"
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
        buttonText: "Mesura",
        lengthMenuText: "Longitud",
        areaMenuText: "Àrea",
        lengthTooltip: "Mesura Longitud",
        areaTooltip: "Mesura Àrea",
        measureTooltip: "Mesura"
    },

    "gxp.plugins.Navigation.prototype": {
        menuText: "Desplaça mapa",
        tooltip: "Desplaça mapa"
    },

    "gxp.plugins.NavigationHistory.prototype": {
        previousMenuText: "Vista anterior",
        nextMenuText: "Vista següent",
        previousTooltip: "Vista anterior",
        nextTooltip: "Vista següent"
    },

    "gxp.plugins.OSMSource.prototype": {
        title: "Capes OpenStreetMap",
        mapnikAttribution: "Dades CC-By-SA de <a href='http://openstreetmap.org/'>OpenStreetMap</a>",
        osmarenderAttribution: "Daded CC-By-SA de <a href='http://openstreetmap.org/'>OpenStreetMap</a>"
    },

    "gxp.plugins.Print.prototype": {
        buttonText:"Imprimeix",
        menuText: "Imprimeix mapa",
        tooltip: "Imprimeix mapa",
        previewText: "Vista prèvia",
        notAllNotPrintableText: "No es poden imprimir totes les capes",
        nonePrintableText: "No es pot imprimir cap de les capes del mapa"
    },

    "gxp.plugins.MapQuestSource.prototype": {
        title: "MapQuest Layers",
        osmAttribution: "Tessel·les cortesia de <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        osmTitle: "MapQuest OpenStreetMap",
        naipAttribution: "Tessel·les cortesia de <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",
        naipTitle: "MapQuest Imatge"
    },

    "gxp.plugins.QueryForm.prototype": {
        queryActionText: "Consulta",
        queryMenuText: "Consulta layer",
        queryActionTip: "Consulta la capa sel·leccionada",
        queryByLocationText: "Query by current map extent",
        queryByAttributesText: "Consulta per atributs",
        queryMsg: "Consultant...",
        cancelButtonText: "Cancel·la",
        noFeaturesTitle: "Sense coincidències",
        noFeaturesMessage: "La vostra consulta no ha produït resultats."
    },

    "gxp.plugins.RemoveLayer.prototype": {
        removeMenuText: "Elimina Capa",
        removeActionTip: "Elimina Capa"
    },
    
    "gxp.plugins.Styler.prototype": {
        menuText: "Edita Estils",
        tooltip: "Gestiona els estils de les capes"
    },

    "gxp.plugins.WMSGetFeatureInfo.prototype": {
        buttonText:"Identify",
        infoActionTip: "Consulta elements",
        popupTitle: "Informació dels elements"
    },

    "gxp.plugins.Zoom.prototype": {
        zoomMenuText: "Zoom Box",
        zoomInMenuText: "Apropa",
        zoomOutMenuText: "Allunya",
        zoomTooltip: "Zoom by dragging a box",
        zoomInTooltip: "Apropa",
        zoomOutTooltip: "Allunya"
    },
    
    "gxp.plugins.ZoomToExtent.prototype": {
        menuText: "Mostra l'extensió total",
        tooltip: "Mostra l'extensió total"
    },
    
    "gxp.plugins.ZoomToDataExtent.prototype": {
        menuText: "Mostra tota la capa",
        tooltip: "Mostra tota la capa"
    },

    "gxp.plugins.ZoomToLayerExtent.prototype": {
        menuText: "Mostra tota la capa",
        tooltip: "Mostra tota la capa"
    },
    
    "gxp.plugins.ZoomToSelectedFeatures.prototype": {
        menuText: "Mostra els elements seleccionats",
        tooltip: "Mostra els elements seleccionats"
    },

    "gxp.FeatureEditPopup.prototype": {
        closeMsgTitle: "Desitgeu desar els canvis?",
        closeMsg: "Els canvis en aquest element no s'han desat. Desitja desar-los?",
        deleteMsgTitle: "Desitgeu esborrar l'element?",
        deleteMsg: "Esteu segurs de voler esborrar aquest element?",
        editButtonText: "Edita",
        editButtonTooltip: "Fes que aquest element sigui editable",
        deleteButtonText: "Esborra",
        deleteButtonTooltip: "Esborra aquest element",
        cancelButtonText: "Cancel·la",
        cancelButtonTooltip: "Deixa d'editar, descarta els canvis",
        saveButtonText: "Desa",
        saveButtonTooltip: "Desa els canvis"
    },
    
    "gxp.FillSymbolizer.prototype": {
        fillText: "Farcit",
        colorText: "Color",
        opacityText: "Opacitat"
    },
    
    "gxp.FilterBuilder.prototype": {
        builderTypeNames: ["alguna de", "totes", "cap de", "no totes"],
        preComboText: "Acompleix",
        postComboText: "les condicions següents:",
        addConditionText: "afegeix condició",
        addGroupText: "afegeix grup",
        removeConditionText: "treu condició"
    },
    
    "gxp.grid.CapabilitiesGrid.prototype": {
        nameHeaderText : "Nom",
        titleHeaderText : "Títol",
        queryableHeaderText : "Consultable",
        layerSelectionLabel: "Llista les capes de:",
        layerAdditionLabel: "o afegeix un altre servidor.",
        expanderTemplateText: "<p><b>Resum:</b> {abstract}</p>"
    },
    
    "gxp.PointSymbolizer.prototype": {
        graphicCircleText: "cercle",
        graphicSquareText: "quadrat",
        graphicTriangleText: "triangle",
        graphicStarText: "estrella",
        graphicCrossText: "creu",
        graphicXText: "x",
        graphicExternalText: "extern",
        urlText: "URL",
        opacityText: "opacitat",
        symbolText: "Símbol",
        sizeText: "Mides",
        rotationText: "Gir"
    },

    "gxp.QueryPanel.prototype": {
        queryByLocationText: "Consulta per lloc",
        currentTextText: "Vista actual",
        queryByAttributesText: "Consulta per atributs",
        layerText: "Capa"
    },
    
    "gxp.RulePanel.prototype": {
        scaleSliderTemplate: "{scaleType} Escala 1:{scale}",
        labelFeaturesText: "Etiqueta elements",
        labelsText: "Etiquetes",
        basicText: "Bàsic",
        advancedText: "Avançat",
        limitByScaleText: "Restringeix per escala",
        limitByConditionText: "Restringeix per condició",
        symbolText: "Símbol",
        nameText: "Nom"
    },
    
    "gxp.ScaleLimitPanel.prototype": {
        scaleSliderTemplate: "{scaleType} Escala 1:{scale}",
        minScaleLimitText: "Escala mínima",
        maxScaleLimitText: "Escala màxima"
    },
    
    "gxp.StrokeSymbolizer.prototype": {
        solidStrokeName: "continu",
        dashStrokeName: "guions",
        dotStrokeName: "punts",
        titleText: "Traç",
        styleText: "Estil",
        colorText: "Color",
        widthText: "Amplada",
        opacityText: "Opacitad"
    },
    
    "gxp.StylePropertiesDialog.prototype": {   
        titleText: "General",
        nameFieldText: "Nom",
        titleFieldText: "Títol",
        abstractFieldText: "Resum"
    },
    
    "gxp.TextSymbolizer.prototype": {
        labelValuesText: "Etiquetatge",
        haloText: "Halo",
        sizeText: "Mida"
    },
    
    "gxp.WMSLayerPanel.prototype": {
        aboutText: "Quant a",
        titleText: "Títol",
        nameText: "Nom",
        descriptionText: "Descripció",
        displayText: "Mostra",
        opacityText: "Opacitat",
        formatText: "Format",
        transparentText: "Transparent",
        cacheText: "Caché",
        cacheFieldText: "Utiliza la versió en caché",
        stylesText: "Estils",
        infoFormatText: "Info format",
        infoFormatEmptyText: "Select a format"
    },

    "gxp.EmbedMapDialog.prototype": {
        publishMessage: "Ja podeu incloure el vostre mapa a altres webs! Simplement copieu el següent codi HTML allà on desitgeu incrustar-ho:",
        heightLabel: 'Alçària',
        widthLabel: 'Amplada',
        mapSizeLabel: 'Mida',
        miniSizeLabel: 'Mínima',
        smallSizeLabel: 'Petita',
        premiumSizeLabel: 'Premium',
        largeSizeLabel: 'Gran'
   },
    
    "gxp.WMSStylesDialog.prototype": {
        addStyleText: "Afegeix",
        addStyleTip: "Afegeix nou estil",
        chooseStyleText: "Escull estil",
        deleteStyleText: "Treu",
        deleteStyleTip: "Esborra l'estil sel·leccionat",
        editStyleText: "Canvia",
        editStyleTip: "Edita l'estil sel·leccionat",
        duplicateStyleText: "Clona",
        duplicateStyleTip: "Duplica l'estil sel·leccionat",
        addRuleText: "Afegeix",
        addRuleTip: "Afegeix nova regla",
        newRuleText: "Nova regla",
        deleteRuleText: "Treu",
        deleteRuleTip: "Esborra la regla sel·leccionada",
        editRuleText: "Edita",
        editRuleTip: "Edita la regla sel·leccionada",
        duplicateRuleText: "Clona",
        duplicateRuleTip: "Duplica la regla sel·leccionada",
        cancelText: "Cancel·la",
        saveText: "Desa",
        styleWindowTitle: "Estil: {0}",
        ruleWindowTitle: "Regla: {0}",
        stylesFieldsetTitle: "Estils",
        rulesFieldsetTitle: "Regles"
    },

    "gxp.LayerUploadPanel.prototype": {
        titleLabel: "Títol",
        titleEmptyText: "Títol de la capa",
        abstractLabel: "Descripció",
        abstractEmptyText: "Descripció de la capa",
        fileLabel: "Dades",
        fieldEmptyText: "Navegueu per les dades...",
        uploadText: "Puja",
        waitMsgText: "Pugeu les vostres dades...",
        invalidFileExtensionText: "L'extensió del fitxer ha de ser alguna d'aquestes: ",
        optionsText: "Opcions",
        workspaceLabel: "Espai de treball",
        workspaceEmptyText: "Espai de treball per defecte",
        dataStoreLabel: "Magatzem",
        dataStoreEmptyText: "Create new store",
        defaultDataStoreEmptyText: "Magatzem de dades per defecte"
    },
    
    "gxp.NewSourceDialog.prototype": {
        title: "Afegeix Servidor...",
        cancelText: "Cancel·la",
        addServerText: "Afegeix Servidor",
        invalidURLText: "Enter a valid URL to a WMS endpoint (e.g. http://example.com/geoserver/wms)",
        contactingServerText: "Connectant amb el Servidor..."
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
